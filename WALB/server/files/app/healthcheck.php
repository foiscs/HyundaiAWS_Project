<?php
// 간단한 헬스체크
http_response_code(200);
echo json_encode([
    'status' => 'healthy',
    'timestamp' => date('Y-m-d H:i:s'),
    'php_version' => PHP_VERSION
]);
?>