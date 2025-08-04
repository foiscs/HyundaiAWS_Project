#!/usr/bin/env python3
import boto3
import json
import gzip
import base64
import time
import logging
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor
import threading

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KinesisSplunkForwarder:
    def __init__(self, region_name=None):
        # 환경변수에서 AWS 설정 읽기
        self.region_name = region_name or os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-2')
        self.account_id = os.getenv('AWS_ACCOUNT_ID')
        
        # AWS 클라이언트 초기화
        if os.getenv('AUTH_MODE') == 'accesskey':
            self.kinesis_client = boto3.client(
                'kinesis',
                region_name=self.region_name,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        else:
            self.kinesis_client = boto3.client('kinesis', region_name=self.region_name)
        
        # 계정 ID가 없으면 STS에서 가져오기
        if not self.account_id:
            try:
                sts_client = boto3.client('sts', region_name=self.region_name)
                self.account_id = sts_client.get_caller_identity()['Account']
            except Exception as e:
                logger.error(f"AWS 계정 ID를 가져올 수 없습니다: {e}")
                self.account_id = "unknown"
        
        # 기본 로그 디렉토리 설정
        base_log_dir = f"/var/log/splunk/{self.account_id}"
        
        # 스트림별 설정 - 환경변수 기반으로 로그 경로 설정
        self.streams_config = {
            'cloudtrail-stream': {
                'log_file': f'{base_log_dir}/cloudtrail.log',
                'service_name': 'cloudtrail'
            },
            'guardduty-stream': {
                'log_file': f'{base_log_dir}/guardduty.log',
                'service_name': 'guardduty'
            },
            'security-hub-stream': {
                'log_file': f'{base_log_dir}/security-hub.log',
                'service_name': 'security-hub'
            }
        }
        
        # 로그 디렉토리 생성
        self._create_log_directories()
        
        # 각 스트림별 shard iterator 저장
        self.shard_iterators = {}
        self.running = True
        
        logger.info(f"Kinesis Splunk Forwarder 초기화 완료")
        logger.info(f"AWS Region: {self.region_name}")
        logger.info(f"AWS Account ID: {self.account_id}")
        logger.info(f"Base Log Directory: {base_log_dir}")
        
    def _create_log_directories(self):
        """로그 디렉토리 생성"""
        try:
            for config in self.streams_config.values():
                log_dir = os.path.dirname(config['log_file'])
                os.makedirs(log_dir, exist_ok=True)
                logger.info(f"로그 디렉토리 생성/확인: {log_dir}")
                
                # splunk 사용자 권한 설정 (splunk 사용자가 있는 경우)
                try:
                    import pwd
                    import grp
                    splunk_uid = pwd.getpwnam('splunk').pw_uid
                    splunk_gid = grp.getgrnam('splunk').gr_gid
                    os.chown(log_dir, splunk_uid, splunk_gid)
                    logger.info(f"splunk 사용자 권한 설정 완료: {log_dir}")
                except (KeyError, OSError) as e:
                    logger.warning(f"splunk 사용자 권한 설정 실패 (정상적일 수 있음): {e}")
                    
        except Exception as e:
            logger.error(f"로그 디렉토리 생성 중 오류: {e}")
            
    def _get_initial_shard_iterator(self, stream_name, shard_id):
        """초기 shard iterator 획득"""
        try:
            response = self.kinesis_client.get_shard_iterator(
                StreamName=stream_name,
                ShardId=shard_id,
                ShardIteratorType='LATEST'  # 최신 데이터부터 읽기
            )
            return response['ShardIterator']
        except Exception as e:
            logger.error(f"Error getting shard iterator for {stream_name}: {e}")
            return None
    
    def _get_stream_shards(self, stream_name):
        """스트림의 모든 shard 조회"""
        try:
            response = self.kinesis_client.describe_stream(StreamName=stream_name)
            return response['StreamDescription']['Shards']
        except Exception as e:
            logger.error(f"Error describing stream {stream_name}: {e}")
            return []
    
    def _decode_cloudwatch_logs(self, data):
        """CloudWatch Logs 데이터 디코딩"""
        try:
            # Base64 디코딩 후 gzip 압축 해제
            try:
                compressed_data = base64.b64decode(data)
                decompressed_data = gzip.decompress(compressed_data)
            except:
                decompressed_data = gzip.decompress(data)

            log_events = json.loads(decompressed_data.decode('utf-8'))
            return log_events
        except Exception as e:
            logger.error(f"Error decoding CloudWatch logs data: {e}")
            return None
    
    def _process_cloudtrail_record(self, record):
        """CloudTrail 레코드 처리"""
        try:
            decoded_data = self._decode_cloudwatch_logs(record['Data'])
            if decoded_data and 'logEvents' in decoded_data:
                processed_events = []
                for event in decoded_data['logEvents']:
                    # CloudTrail 로그는 이미 JSON 형태
                    if event['message'].strip():
                        try:
                            # JSON 파싱 시도
                            log_data = json.loads(event['message'])
                            processed_events.append({
                                'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                                'service': 'cloudtrail',
                                'account_id': self.account_id,
                                'data': log_data
                            })
                        except json.JSONDecodeError:
                            # 일반 텍스트 로그인 경우
                            processed_events.append({
                                'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                                'service': 'cloudtrail',
                                'account_id': self.account_id,
                                'message': event['message']
                            })
                return processed_events
        except Exception as e:
            logger.error(f"CloudTrail 레코드 처리 중 오류: {e}")
        return []
    
    def _process_guardduty_record(self, record):
        """GuardDuty 레코드 처리"""
        try:
            decoded_data = self._decode_cloudwatch_logs(record['Data'])
            if decoded_data and 'logEvents' in decoded_data:
                processed_events = []
                for event in decoded_data['logEvents']:
                    if event['message'].strip():
                        try:
                            log_data = json.loads(event['message'])
                            processed_events.append({
                                'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                                'service': 'guardduty',
                                'account_id': self.account_id,
                                'data': log_data
                            })
                        except json.JSONDecodeError:
                            processed_events.append({
                                'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                                'service': 'guardduty',
                                'account_id': self.account_id,
                                'message': event['message']
                            })
                return processed_events
        except Exception as e:
            logger.error(f"GuardDuty 레코드 처리 중 오류: {e}")
        return []
    
    def _process_securityhub_record(self, record):
        """Security Hub 레코드 처리"""
        try:
            decoded_data = self._decode_cloudwatch_logs(record['Data'])
            if decoded_data and 'logEvents' in decoded_data:
                processed_events = []
                for event in decoded_data['logEvents']:
                    if event['message'].strip():
                        try:
                            log_data = json.loads(event['message'])
                            processed_events.append({
                                'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                                'service': 'security-hub',
                                'account_id': self.account_id,
                                'data': log_data
                            })
                        except json.JSONDecodeError:
                            processed_events.append({
                                'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                                'service': 'security-hub',
                                'account_id': self.account_id,
                                'message': event['message']
                            })
                return processed_events
        except Exception as e:
            logger.error(f"Security Hub 레코드 처리 중 오류: {e}")
        return []
    
    def _write_to_log_file(self, log_file, events):
        """로그 파일에 이벤트 쓰기"""
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                for event in events:
                    log_line = json.dumps(event, ensure_ascii=False, separators=(',', ':'))
                    f.write(log_line + '\n')
            logger.debug(f"{len(events)}개 이벤트를 {log_file}에 기록했습니다")
        except Exception as e:
            logger.error(f"로그 파일 쓰기 오류 {log_file}: {e}")
    
    def _process_stream_records(self, stream_name, records):
        """스트림 레코드 처리"""
        if not records:
            return
            
        config = self.streams_config.get(stream_name)
        if not config:
            logger.warning(f"알 수 없는 스트림: {stream_name}")
            return
            
        all_events = []
        
        for record in records:
            try:
                # 서비스별 레코드 처리
                if 'cloudtrail' in stream_name:
                    events = self._process_cloudtrail_record(record)
                elif 'guardduty' in stream_name:
                    events = self._process_guardduty_record(record)
                elif 'security-hub' in stream_name:
                    events = self._process_securityhub_record(record)
                else:
                    logger.warning(f"처리할 수 없는 스트림 타입: {stream_name}")
                    continue
                    
                all_events.extend(events)
                
            except Exception as e:
                logger.error(f"레코드 처리 중 오류 ({stream_name}): {e}")
        
        if all_events:
            self._write_to_log_file(config['log_file'], all_events)
            logger.info(f"{stream_name}에서 {len(all_events)}개 이벤트 처리 완료")
    
    def _consume_stream(self, stream_name):
        """개별 스트림 소비"""
        logger.info(f"{stream_name} 스트림 소비 시작")
        
        # 스트림의 모든 shard 가져오기
        shards = self._get_stream_shards(stream_name)
        if not shards:
            logger.warning(f"{stream_name} 스트림에 shard가 없습니다")
            return
        
        # 각 shard에 대한 iterator 초기화
        for shard in shards:
            shard_id = shard['ShardId']
            iterator = self._get_initial_shard_iterator(stream_name, shard_id)
            if iterator:
                if stream_name not in self.shard_iterators:
                    self.shard_iterators[stream_name] = {}
                self.shard_iterators[stream_name][shard_id] = iterator
        
        # 스트림 데이터 읽기 루프
        while self.running:
            try:
                if stream_name not in self.shard_iterators:
                    logger.warning(f"{stream_name}에 대한 shard iterator가 없습니다")
                    time.sleep(10)
                    continue
                
                for shard_id, iterator in list(self.shard_iterators[stream_name].items()):
                    if not iterator:
                        continue
                        
                    try:
                        response = self.kinesis_client.get_records(
                            ShardIterator=iterator,
                            Limit=100  # 한 번에 처리할 레코드 수
                        )
                        
                        records = response.get('Records', [])
                        if records:
                            self._process_stream_records(stream_name, records)
                        
                        # 다음 iterator 업데이트
                        next_iterator = response.get('NextShardIterator')
                        if next_iterator:
                            self.shard_iterators[stream_name][shard_id] = next_iterator
                        else:
                            # Shard가 닫힌 경우
                            logger.info(f"{stream_name}의 {shard_id} shard가 닫혔습니다")
                            del self.shard_iterators[stream_name][shard_id]
                        
                    except Exception as e:
                        logger.error(f"{stream_name}의 {shard_id} 처리 중 오류: {e}")
                        time.sleep(5)
                
                time.sleep(1)  # 1초 대기
                
            except Exception as e:
                logger.error(f"{stream_name} 스트림 소비 중 오류: {e}")
                time.sleep(10)
    
    def start_forwarding(self):
        """모든 스트림에 대한 포워딩 시작"""
        logger.info("Kinesis Splunk Forwarder 시작")
        
        # 각 스트림에 대해 별도 스레드로 실행
        with ThreadPoolExecutor(max_workers=len(self.streams_config)) as executor:
            futures = []
            for stream_name in self.streams_config.keys():
                future = executor.submit(self._consume_stream, stream_name)
                futures.append(future)
            
            try:
                # 모든 스레드 완료 대기
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                logger.info("종료 신호 받음")
                self.running = False
            except Exception as e:
                logger.error(f"포워딩 중 오류: {e}")
                self.running = False
    
    def stop(self):
        """포워딩 중지"""
        logger.info("Kinesis Splunk Forwarder 중지")
        self.running = False

def main():
    """메인 함수"""
    # 환경변수 확인
    required_env_vars = ['AWS_DEFAULT_REGION', 'AWS_ACCOUNT_ID']
    for var in required_env_vars:
        if not os.getenv(var):
            logger.warning(f"환경변수 {var}가 설정되지 않았습니다")
    
    # 인증 모드 확인
    auth_mode = os.getenv('AUTH_MODE', 'default')
    if auth_mode == 'accesskey':
        if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
            logger.error("Access Key 인증 모드이지만 AWS_ACCESS_KEY_ID 또는 AWS_SECRET_ACCESS_KEY가 설정되지 않았습니다")
            return
    
    try:
        forwarder = KinesisSplunkForwarder()
        forwarder.start_forwarding()
    except Exception as e:
        logger.error(f"Forwarder 실행 중 오류: {e}")
    finally:
        logger.info("Kinesis Splunk Forwarder 종료")

if __name__ == "__main__":
    main()