<?php
require_once __DIR__ . '/../../vendor/autoload.php';

use Aws\S3\S3Client;
use Aws\S3\Exception\S3Exception;

class S3FileManager {
    private $s3Client;
    private $bucket;
    private $region;
    private $cloudfrontUrl;
    private $isEnabled;
    
    public function __construct() {
        $this->bucket = $_ENV['AWS_S3_BUCKET'] ?? 'test-simpleblog-files';
        $this->region = $_ENV['AWS_S3_REGION'] ?? 'ap-northeast-2';
        $this->cloudfrontUrl = $_ENV['AWS_S3_CLOUDFRONT_URL'] ?? '';
        
        try {
            // IAM 역할을 사용한 S3 클라이언트 생성
            // EC2 인스턴스에서 실행될 때 자동으로 IAM 역할 자격 증명을 사용
            $this->s3Client = new S3Client([
                'version' => 'latest',
                'region' => $this->region,
                // credentials를 명시하지 않으면 자동으로 IAM 역할을 사용
            ]);
            
            // S3 연결 테스트
            $this->s3Client->headBucket(['Bucket' => $this->bucket]);
            $this->isEnabled = true;
            
            error_log("S3 클라이언트가 IAM 역할로 성공적으로 초기화되었습니다.");
            
        } catch (S3Exception $e) {
            error_log("S3 연결 실패: " . $e->getMessage());
            $this->isEnabled = false;
        } catch (Exception $e) {
            error_log("S3 클라이언트 초기화 실패: " . $e->getMessage());
            $this->isEnabled = false;
        }
    }
    
    public function isS3Enabled() {
        return $this->isEnabled;
    }
    
    public function uploadFile($file, $type = 'images') {
        if (!$this->isEnabled) {
            // S3가 비활성화된 경우 로컬 파일 시스템 사용
            return $this->uploadFileLocal($file, $type);
        }
        
        $fileName = $this->generateSafeFilename($file['name']);
        $s3Key = $type . '/' . $fileName;
        
        try {
            $result = $this->s3Client->putObject([
                'Bucket' => $this->bucket,
                'Key' => $s3Key,
                'Body' => fopen($file['tmp_name'], 'r'),
                'ContentType' => $file['type'],
                'ACL' => 'private',
                'ServerSideEncryption' => 'AES256'
            ]);
            
            $fileUrl = $this->cloudfrontUrl ? 
                $this->cloudfrontUrl . '/' . $s3Key : 
                "https://{$this->bucket}.s3.{$this->region}.amazonaws.com/{$s3Key}";
            
            return [
                'original_name' => $file['name'],
                'stored_name' => $fileName,
                'file_path' => $fileUrl,
                's3_key' => $s3Key,
                'file_size' => $file['size'],
                'mime_type' => $file['type']
            ];
            
        } catch (S3Exception $e) {
            error_log("S3 업로드 실패: " . $e->getMessage());
            throw new Exception('S3 업로드 실패: ' . $e->getMessage());
        }
    }
    
    public function deleteFile($s3Key) {
        if (!$this->isEnabled) {
            return $this->deleteFileLocal($s3Key);
        }
        
        try {
            $this->s3Client->deleteObject([
                'Bucket' => $this->bucket,
                'Key' => $s3Key
            ]);
            return true;
        } catch (S3Exception $e) {
            error_log('S3 삭제 실패: ' . $e->getMessage());
            return false;
        }
    }
    
    public function getSignedUrl($s3Key, $expiration = '+20 minutes') {
        if (!$this->isEnabled) {
            return $s3Key; // 로컬 파일 경로 반환
        }
        
        try {
            $cmd = $this->s3Client->getCommand('GetObject', [
                'Bucket' => $this->bucket,
                'Key' => $s3Key
            ]);
            
            $request = $this->s3Client->createPresignedRequest($cmd, $expiration);
            return (string) $request->getUri();
            
        } catch (S3Exception $e) {
            error_log('Signed URL 생성 실패: ' . $e->getMessage());
            throw new Exception('Signed URL 생성 실패: ' . $e->getMessage());
        }
    }
    
    /**
     * 로컬 파일 시스템 업로드 (S3 fallback)
     */
    private function uploadFileLocal($file, $type) {
        $uploadDir = __DIR__ . "/../../uploads/{$type}/" . date('Y/m/');
        
        if (!is_dir($uploadDir)) {
            mkdir($uploadDir, 0755, true);
        }
        
        $fileName = $this->generateSafeFilename($file['name']);
        $filePath = $uploadDir . $fileName;
        
        if (!move_uploaded_file($file['tmp_name'], $filePath)) {
            throw new Exception('로컬 파일 업로드 실패');
        }
        
        $relativePath = "uploads/{$type}/" . date('Y/m/') . $fileName;
        
        return [
            'original_name' => $file['name'],
            'stored_name' => $fileName,
            'file_path' => $relativePath,
            's3_key' => $relativePath,
            'file_size' => $file['size'],
            'mime_type' => $file['type']
        ];
    }
    
    /**
     * 로컬 파일 삭제
     */
    private function deleteFileLocal($filePath) {
        $fullPath = __DIR__ . '/../../' . $filePath;
        
        if (file_exists($fullPath)) {
            return unlink($fullPath);
        }
        
        return true;
    }
    
    private function generateSafeFilename($originalName) {
        $extension = strtolower(pathinfo($originalName, PATHINFO_EXTENSION));
        return uniqid() . '_' . time() . '.' . $extension;
    }
}