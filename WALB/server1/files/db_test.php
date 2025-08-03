<?php
// 데이터베이스 연결 테스트 스크립트
header('Content-Type: application/json');

// 환경변수 읽기
$db_host = $_ENV['DB_HOST'] ?? getenv('DB_HOST') ?: 'localhost';
$db_name = $_ENV['DB_NAME'] ?? getenv('DB_NAME') ?: 'mydb';
$db_user = $_ENV['DB_USER'] ?? getenv('DB_USER') ?: 'dbadmin';
$db_password = $_ENV['DB_PASSWORD'] ?? getenv('DB_PASSWORD') ?: '';
$db_port = $_ENV['DB_PORT'] ?? getenv('DB_PORT') ?: '3306';

$result = [
    'config' => [
        'host' => $db_host,
        'database' => $db_name,
        'user' => $db_user,
        'port' => $db_port,
        'password_length' => strlen($db_password)
    ],
    'connection_test' => null,
    'error' => null
];

try {
    $dsn = "mysql:host={$db_host};port={$db_port};dbname={$db_name};charset=utf8mb4";
    $options = [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
        PDO::ATTR_TIMEOUT => 10,
        PDO::ATTR_PERSISTENT => false,
        PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4"
    ];
    
    $pdo = new PDO($dsn, $db_user, $db_password, $options);
    
    // 연결 테스트
    $stmt = $pdo->query("SELECT VERSION() as version, DATABASE() as current_database, USER() as current_user");
    $db_info = $stmt->fetch();
    
    // 테이블 존재 확인
    $tables_check = [];
    $required_tables = ['users', 'posts', 'images', 'files'];
    
    foreach ($required_tables as $table) {
        $stmt = $pdo->prepare("
            SELECT COUNT(*) > 0 as table_exists
            FROM information_schema.tables 
            WHERE table_schema = ? 
            AND table_name = ?
        ");
        $stmt->execute([$db_name, $table]);
        $tables_check[$table] = (bool)$stmt->fetchColumn();
    }
    
    $result['connection_test'] = 'SUCCESS';
    $result['database_info'] = $db_info;
    $result['tables_check'] = $tables_check;
    
} catch(PDOException $e) {
    $result['connection_test'] = 'FAILED';
    $result['error'] = $e->getMessage();
    $result['error_codes'] = [
        'SQLSTATE' => $e->getCode(),
        'driver_code' => $e->errorInfo[1] ?? null,
        'driver_message' => $e->errorInfo[2] ?? null
    ];
}

echo json_encode($result, JSON_PRETTY_PRINT);
?>