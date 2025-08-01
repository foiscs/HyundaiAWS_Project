<?php
// simple-health.php (livenessProbe 용)
// DB 연결 등 하지 않고 살아있는지만 체크
http_response_code(200);
echo json_encode(['status'=>'ok', 'time'=>date('c')]);
