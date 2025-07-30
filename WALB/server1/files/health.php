<?php
// healthcheck.php (readinessProbe 용)

$db_host = getenv('DB_HOST') ?: 'localhost';
$db_port = getenv('DB_PORT') ?: '5432';
$db_name = getenv('DB_NAME') ?: 'mydb';
$db_user = getenv('DB_USER') ?: 'dbadmin';
$db_pass = getenv('DB_PASSWORD') ?: '';

try {
    $dsn = "pgsql:host=$db_host;port=$db_port;dbname=$db_name;connect_timeout=2";
    $pdo = new PDO($dsn, $db_user, $db_pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_TIMEOUT => 2,
    ]);
    // 연결 성공 = ready
    http_response_code(200);
    echo json_encode(['status'=>'ok', 'db'=>'connected', 'time'=>date('c')]);
} catch (Exception $e) {
    http_response_code(503);
    echo json_encode(['status'=>'fail', 'error'=>$e->getMessage()]);
}
?>
