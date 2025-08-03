<?php
// 데이터베이스 연결 성능 진단 스크립트
header('Content-Type: application/json');

// 시간 측정 시작
$start_time = microtime(true);

// 환경변수 로드
$db_host = $_ENV['DB_HOST'] ?? getenv('DB_HOST') ?: 'walb-mysql-rds.cx02kko4cplr.ap-northeast-2.rds.amazonaws.com';
$db_name = $_ENV['DB_NAME'] ?? getenv('DB_NAME') ?: 'mydb';
$db_user = $_ENV['DB_USER'] ?? getenv('DB_USER') ?: 'dbadmin';
$db_password = $_ENV['DB_PASSWORD'] ?? getenv('DB_PASSWORD') ?: 'MySecurePassword123!';
$db_port = $_ENV['DB_PORT'] ?? getenv('DB_PORT') ?: '3306';

$result = [
    'tests' => [],
    'summary' => [],
    'recommendations' => []
];

// 1. DNS 해상도 테스트
$dns_start = microtime(true);
$ip_address = gethostbyname($db_host);
$dns_time = (microtime(true) - $dns_start) * 1000;

$result['tests']['dns_resolution'] = [
    'hostname' => $db_host,
    'resolved_ip' => $ip_address,
    'time_ms' => round($dns_time, 2),
    'status' => $ip_address !== $db_host ? 'success' : 'failed'
];

// 2. TCP 연결 테스트
$tcp_start = microtime(true);
$socket = @fsockopen($db_host, $db_port, $errno, $errstr, 5);
$tcp_time = (microtime(true) - $tcp_start) * 1000;

$result['tests']['tcp_connection'] = [
    'host' => $db_host,
    'port' => $db_port,
    'time_ms' => round($tcp_time, 2),
    'status' => $socket ? 'success' : 'failed',
    'error' => $socket ? null : "$errno: $errstr"
];

if ($socket) {
    fclose($socket);
}

// 3. PDO 연결 테스트 (여러 설정으로)
$connection_tests = [
    'default' => [
        PDO::ATTR_TIMEOUT => 30,
        PDO::ATTR_PERSISTENT => true
    ],
    'fast_timeout' => [
        PDO::ATTR_TIMEOUT => 5,
        PDO::ATTR_PERSISTENT => false
    ],
    'optimized' => [
        PDO::ATTR_TIMEOUT => 10,
        PDO::ATTR_PERSISTENT => false,
        PDO::ATTR_EMULATE_PREPARES => false,
        PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4"
    ]
];

foreach ($connection_tests as $test_name => $options) {
    $pdo_start = microtime(true);
    try {
        $dsn = "mysql:host={$db_host};port={$db_port};dbname={$db_name};charset=utf8mb4";
        $default_options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ];
        
        $pdo = new PDO($dsn, $db_user, $db_password, array_merge($default_options, $options));
        
        // 간단한 쿼리 실행
        $query_start = microtime(true);
        $stmt = $pdo->query("SELECT 1 as test");
        $query_result = $stmt->fetch();
        $query_time = (microtime(true) - $query_start) * 1000;
        
        $total_time = (microtime(true) - $pdo_start) * 1000;
        
        $result['tests']["pdo_connection_$test_name"] = [
            'connection_time_ms' => round($total_time, 2),
            'query_time_ms' => round($query_time, 2),
            'total_time_ms' => round($total_time + $query_time, 2),
            'status' => 'success',
            'options' => $options,
            'query_result' => $query_result
        ];
        
        $pdo = null; // 연결 해제
        
    } catch (PDOException $e) {
        $total_time = (microtime(true) - $pdo_start) * 1000;
        $result['tests']["pdo_connection_$test_name"] = [
            'connection_time_ms' => round($total_time, 2),
            'status' => 'failed',
            'error' => $e->getMessage(),
            'options' => $options
        ];
    }
}

// 4. 여러 연속 연결 테스트 (연결 풀링 효과 확인)
$consecutive_times = [];
for ($i = 0; $i < 5; $i++) {
    $conn_start = microtime(true);
    try {
        $dsn = "mysql:host={$db_host};port={$db_port};dbname={$db_name};charset=utf8mb4";
        $pdo = new PDO($dsn, $db_user, $db_password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_PERSISTENT => true,
            PDO::ATTR_TIMEOUT => 10,
            PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4"
        ]);
        $pdo->query("SELECT 1");
        $consecutive_times[] = round((microtime(true) - $conn_start) * 1000, 2);
        $pdo = null;
    } catch (PDOException $e) {
        $consecutive_times[] = 'failed: ' . $e->getMessage();
    }
}

$result['tests']['consecutive_connections'] = [
    'times_ms' => $consecutive_times,
    'avg_time_ms' => round(array_sum(array_filter($consecutive_times, 'is_numeric')) / count(array_filter($consecutive_times, 'is_numeric')), 2)
];

// 5. 네트워크 정보 수집
$result['tests']['network_info'] = [
    'server_location' => gethostname(),
    'php_version' => phpversion(),
    'pdo_mysql_version' => phpversion('pdo_mysql'),
    'memory_limit' => ini_get('memory_limit'),
    'max_execution_time' => ini_get('max_execution_time')
];

// 총 실행 시간
$total_execution_time = (microtime(true) - $start_time) * 1000;

// 문제 분석 및 권장사항
$result['summary'] = [
    'total_execution_time_ms' => round($total_execution_time, 2),
    'dns_resolution_ms' => $result['tests']['dns_resolution']['time_ms'],
    'tcp_connection_ms' => $result['tests']['tcp_connection']['time_ms'],
    'fastest_pdo_connection_ms' => min(array_column(array_filter($result['tests'], function($key) {
        return strpos($key, 'pdo_connection_') === 0;
    }, ARRAY_FILTER_USE_KEY), 'connection_time_ms'))
];

// 권장사항 생성
if ($result['tests']['dns_resolution']['time_ms'] > 100) {
    $result['recommendations'][] = "DNS 해상도가 느림 ({$result['tests']['dns_resolution']['time_ms']}ms). /etc/hosts에 IP 직접 매핑 고려";
}

if ($result['tests']['tcp_connection']['time_ms'] > 50) {
    $result['recommendations'][] = "TCP 연결이 느림 ({$result['tests']['tcp_connection']['time_ms']}ms). 네트워크 지연 또는 보안그룹 확인 필요";
}

if (isset($result['tests']['consecutive_connections']['avg_time_ms']) && 
    $result['tests']['consecutive_connections']['avg_time_ms'] > $result['tests']['pdo_connection_fast_timeout']['connection_time_ms']) {
    $result['recommendations'][] = "연결 풀링이 효과적이지 않음. 연결 설정 최적화 필요";
}

if ($result['summary']['fastest_pdo_connection_ms'] > 200) {
    $result['recommendations'][] = "PDO 연결이 매우 느림 ({$result['summary']['fastest_pdo_connection_ms']}ms). RDS 인스턴스 성능 점검 필요";
}

echo json_encode($result, JSON_PRETTY_PRINT);
?>