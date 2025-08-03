<?php
// 상세한 헬스체크 (DB 연결 포함)
$start_time = microtime(true);

try {
    // 환경변수 로드
    $db_host = $_ENV['DB_HOST'] ?? getenv('DB_HOST') ?: 'localhost';
    $db_name = $_ENV['DB_NAME'] ?? getenv('DB_NAME') ?: 'mydb';
    $db_user = $_ENV['DB_USER'] ?? getenv('DB_USER') ?: 'dbadmin';
    $db_password = $_ENV['DB_PASSWORD'] ?? getenv('DB_PASSWORD') ?: '';
    $db_port = $_ENV['DB_PORT'] ?? getenv('DB_PORT') ?: '3306';
    
    $health_data = [
        'status' => 'healthy',
        'timestamp' => date('Y-m-d H:i:s'),
        'php_version' => PHP_VERSION,
        'pdo_mysql_loaded' => extension_loaded('pdo_mysql'),
        'available_drivers' => PDO::getAvailableDrivers(),
        'memory_usage' => [
            'current' => round(memory_get_usage(true) / 1024 / 1024, 2) . 'MB',
            'peak' => round(memory_get_peak_usage(true) / 1024 / 1024, 2) . 'MB'
        ]
    ];
    
    // 데이터베이스 연결 테스트
    $db_start = microtime(true);
    
    // DNS 해상도 시간 측정
    $dns_start = microtime(true);
    $ip = gethostbyname($db_host);
    $dns_time = (microtime(true) - $dns_start) * 1000;
    
    // TCP 연결 시간 측정
    $tcp_start = microtime(true);
    $socket = @fsockopen($db_host, $db_port, $errno, $errstr, 5);
    $tcp_time = (microtime(true) - $tcp_start) * 1000;
    
    if ($socket) {
        fclose($socket);
        
        // PDO 연결 시간 측정
        $pdo_start = microtime(true);
        $dsn = "mysql:host={$db_host};port={$db_port};dbname={$db_name};charset=utf8mb4";
        $pdo = new PDO($dsn, $db_user, $db_password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_TIMEOUT => 5,
            PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4"
        ]);
        
        // 간단한 쿼리 실행
        $query_start = microtime(true);
        $stmt = $pdo->query("SELECT VERSION() as version, DATABASE() as current_database, CONNECTION_ID() as connection_id");
        $db_info = $stmt->fetch();
        $query_time = (microtime(true) - $query_start) * 1000;
        
        $pdo_time = (microtime(true) - $pdo_start) * 1000;
        $total_db_time = (microtime(true) - $db_start) * 1000;
        
        $health_data['database'] = [
            'status' => 'connected',
            'host' => $db_host,
            'resolved_ip' => $ip,
            'port' => $db_port,
            'database' => $db_name,
            'timing' => [
                'dns_resolution_ms' => round($dns_time, 2),
                'tcp_connection_ms' => round($tcp_time, 2),
                'pdo_connection_ms' => round($pdo_time, 2),
                'query_execution_ms' => round($query_time, 2),
                'total_time_ms' => round($total_db_time, 2)
            ],
            'server_info' => [
                'version' => $db_info['version'] ?? 'unknown',
                'database' => $db_info['current_database'] ?? 'unknown',
                'connection_id' => $db_info['connection_id'] ?? 'unknown'
            ]
        ];
        
        // 성능 경고
        $warnings = [];
        if ($dns_time > 100) $warnings[] = "DNS resolution slow ({$dns_time}ms)";
        if ($tcp_time > 50) $warnings[] = "TCP connection slow ({$tcp_time}ms)";
        if ($pdo_time > 200) $warnings[] = "PDO connection slow ({$pdo_time}ms)";
        if ($query_time > 100) $warnings[] = "Query execution slow ({$query_time}ms)";
        
        if (!empty($warnings)) {
            $health_data['warnings'] = $warnings;
        }
        
    } else {
        $health_data['database'] = [
            'status' => 'tcp_failed',
            'host' => $db_host,
            'port' => $db_port,
            'error' => "$errno: $errstr",
            'timing' => [
                'dns_resolution_ms' => round($dns_time, 2),
                'tcp_connection_ms' => round($tcp_time, 2)
            ]
        ];
        $health_data['status'] = 'degraded';
    }
    
} catch (PDOException $e) {
    $health_data['database'] = [
        'status' => 'pdo_failed',
        'host' => $db_host ?? 'unknown',
        'error' => $e->getMessage(),
        'timing' => [
            'dns_resolution_ms' => round($dns_time ?? 0, 2),
            'tcp_connection_ms' => round($tcp_time ?? 0, 2),
            'total_attempt_ms' => round((microtime(true) - $db_start) * 1000, 2)
        ]
    ];
    $health_data['status'] = 'unhealthy';
    http_response_code(503);
} catch (Exception $e) {
    $health_data['database'] = [
        'status' => 'error',
        'error' => $e->getMessage()
    ];
    $health_data['status'] = 'unhealthy';
    http_response_code(503);
}

$health_data['total_execution_time_ms'] = round((microtime(true) - $start_time) * 1000, 2);

echo json_encode($health_data, JSON_PRETTY_PRINT);
?>