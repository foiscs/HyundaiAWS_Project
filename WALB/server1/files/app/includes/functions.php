<?php
// Composer autoload 로드
$autoload_paths = [
    __DIR__ . '/../../../vendor/autoload.php',
    __DIR__ . '/../../vendor/autoload.php',  
    __DIR__ . '/../vendor/autoload.php',
];

foreach ($autoload_paths as $autoload_path) {
    if (file_exists($autoload_path)) {
        require_once $autoload_path;
        break;
    }
}

// S3 기능 로드
if (file_exists(__DIR__ . '/s3_functions.php')) {
    require_once 's3_functions.php';
}

// 세션 시작
if (session_status() == PHP_SESSION_NONE) {
    session_start();
}

// 파일 업로드 관련 상수
define('MAX_IMAGE_SIZE', 5 * 1024 * 1024); // 5MB
define('MAX_UPLOADFILE_SIZE', 10 * 1024 * 1024); // 10MB

$allowed_image_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
$allowed_attachment_types = [
    'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/zip', 'text/plain', 'text/csv'
];

// 기본 함수들
function isLoggedIn() {
    return isset($_SESSION['user_id']);
}

function requireLogin() {
    if (!isLoggedIn()) {
        header("Location: login.php");
        exit();
    }
}

function escape($string) {
    return htmlspecialchars($string, ENT_QUOTES, 'UTF-8');
}

function clean($string) {
    return trim(stripslashes($string));
}

function hashPassword($password) {
    return password_hash($password, PASSWORD_DEFAULT);
}

function verifyPassword($password, $hash) {
    return password_verify($password, $hash);
}

function generateCSRFToken() {
    if (!isset($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

function verifyCSRFToken($token) {
    return isset($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
}

function setSuccessMessage($message) {
    $_SESSION['success_message'] = $message;
}

function setErrorMessage($message) {
    $_SESSION['error_message'] = $message;
}

function displayMessages() {
    $output = '';
    
    if (isset($_SESSION['success_message'])) {
        $output .= '<div class="alert alert-success">' . escape($_SESSION['success_message']) . '</div>';
        unset($_SESSION['success_message']);
    }
    
    if (isset($_SESSION['error_message'])) {
        $output .= '<div class="alert alert-error">' . escape($_SESSION['error_message']) . '</div>';
        unset($_SESSION['error_message']);
    }
    
    return $output;
}

function validateEmail($email) {
    return filter_var($email, FILTER_VALIDATE_EMAIL);
}

function validatePassword($password) {
    return strlen($password) >= 6;
}

function validateUsername($username) {
    return preg_match('/^[a-zA-Z0-9_]{3,20}$/', $username);
}

// 파일 타입 검증
function validateFileType($file, $type = 'image') {
    global $allowed_image_types, $allowed_attachment_types;

    $allowed_types = ($type === 'image') ? $allowed_image_types : $allowed_attachment_types;
    
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mime_type = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);

    if (!in_array($mime_type, $allowed_types)) {
        return false;
    }
    
    // 확장자 검증
    $extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
    $allowed_extensions = [];
    
    if ($type === 'image') {
        $allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    } else {
        $allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'txt', 'csv'];
    }
    
    return in_array($extension, $allowed_extensions);
}

// S3 이미지 업로드
function uploadImage($file) {
    // 기본 검증
    if ($file['error'] !== UPLOAD_ERR_OK) {
        throw new Exception('파일 업로드 중 오류가 발생했습니다.');
    }
    
    if ($file['size'] > MAX_IMAGE_SIZE) {
        throw new Exception('이미지 파일 크기는 5MB를 초과할 수 없습니다.');
    }
    
    if (!validateFileType($file, 'image')) {
        throw new Exception('지원하지 않는 이미지 형식입니다. (JPG, PNG, GIF, WEBP만 허용)');
    }
    
    // S3FileManager를 사용한 업로드
    try {
        $s3Manager = new S3FileManager();
        $result = $s3Manager->uploadFile($file, 'images');
        
        // 이미지 리사이징 (S3 URL로 처리)
        // 리사이징이 필요한 경우 여기서 처리
        
        return $result;
    } catch (Exception $e) {
        throw new Exception('S3 이미지 업로드 실패: ' . $e->getMessage());
    }
}

// S3 파일 업로드
function uploadFiles($file) {
    // 기본 검증
    if ($file['error'] !== UPLOAD_ERR_OK) {
        $error_messages = [
            UPLOAD_ERR_INI_SIZE => 'PHP 설정(upload_max_filesize)에서 허용하는 크기를 초과했습니다.',
            UPLOAD_ERR_FORM_SIZE => 'HTML 폼에서 지정한 MAX_FILE_SIZE를 초과했습니다.',
            UPLOAD_ERR_PARTIAL => '파일이 부분적으로만 업로드되었습니다.',
            UPLOAD_ERR_NO_FILE => '파일이 업로드되지 않았습니다.',
            UPLOAD_ERR_NO_TMP_DIR => '임시 디렉토리가 없습니다.',
            UPLOAD_ERR_CANT_WRITE => '디스크에 쓸 수 없습니다.',
            UPLOAD_ERR_EXTENSION => 'PHP 확장에 의해 업로드가 중단되었습니다.'
        ];
        
        $error_msg = $error_messages[$file['error']] ?? '알 수 없는 업로드 오류가 발생했습니다.';
        throw new Exception($error_msg);
    }
    
    if ($file['size'] > MAX_UPLOADFILE_SIZE) {
        throw new Exception('첨부파일 크기는 10MB를 초과할 수 없습니다.');
    }
    
    if (!validateFileType($file, 'attachment')) {
        throw new Exception('지원하지 않는 파일 형식입니다.');
    }
    
    // S3FileManager를 사용한 업로드
    try {
        $s3Manager = new S3FileManager();
        return $s3Manager->uploadFile($file, 'files');
    } catch (Exception $e) {
        throw new Exception('S3 파일 업로드 실패: ' . $e->getMessage());
    }
}

// S3에 이미지 저장
function savePostImages($pdo, $post_id, $images) {
    foreach ($images as $image) {
        $stmt = $pdo->prepare("
            INSERT INTO images (post_id, filename, original_name, file_path, file_size, mime_type) 
            VALUES (?, ?, ?, ?, ?, ?)
        ");
        $stmt->execute([
            $post_id,
            $image['stored_name'],
            $image['original_name'],
            $image['file_path'], // S3 URL
            $image['file_size'],
            $image['mime_type']
        ]);
    }
}

// S3에 파일 저장
function savePostFiles($pdo, $post_id, $attachments) {
    foreach ($attachments as $attachment) {
        $stmt = $pdo->prepare("
            INSERT INTO files (post_id, original_name, file_path, file_size, mime_type) 
            VALUES (?, ?, ?, ?, ?)
        ");
        $stmt->execute([
            $post_id,
            $attachment['original_name'],
            $attachment['file_path'], // S3 URL
            $attachment['file_size'],
            $attachment['mime_type']
        ]);
    }
}

// 게시글 이미지 가져오기
function getPostImages($pdo, $post_id) {
    $stmt = $pdo->prepare("SELECT * FROM images WHERE post_id = ? ORDER BY id");
    $stmt->execute([$post_id]);
    return $stmt->fetchAll();
}

// 게시글 파일 가져오기
function getPostFiles($pdo, $post_id) {
    $stmt = $pdo->prepare("SELECT * FROM files WHERE post_id = ? ORDER BY id");
    $stmt->execute([$post_id]);
    return $stmt->fetchAll();
}

// 여러 게시글의 이미지들을 한번에 가져오기 (성능 최적화)
function getBatchPostImages($pdo, $post_ids) {
    if (empty($post_ids)) return [];
    
    $placeholders = str_repeat('?,', count($post_ids) - 1) . '?';
    $stmt = $pdo->prepare("SELECT * FROM images WHERE post_id IN ($placeholders) ORDER BY post_id, id");
    $stmt->execute($post_ids);
    
    $images_by_post = [];
    while ($row = $stmt->fetch()) {
        $images_by_post[$row['post_id']][] = $row;
    }
    return $images_by_post;
}

// 여러 게시글의 파일들을 한번에 가져오기 (성능 최적화)
function getBatchPostFiles($pdo, $post_ids) {
    if (empty($post_ids)) return [];
    
    $placeholders = str_repeat('?,', count($post_ids) - 1) . '?';
    $stmt = $pdo->prepare("SELECT * FROM files WHERE post_id IN ($placeholders) ORDER BY post_id, id");
    $stmt->execute($post_ids);
    
    $files_by_post = [];
    while ($row = $stmt->fetch()) {
        $files_by_post[$row['post_id']][] = $row;
    }
    return $files_by_post;
}

// 파일 크기 포맷
function formatFileSize($bytes) {
    if ($bytes >= 1073741824) {
        return number_format($bytes / 1073741824, 2) . ' GB';
    } elseif ($bytes >= 1048576) {
        return number_format($bytes / 1048576, 2) . ' MB';
    } elseif ($bytes >= 1024) {
        return number_format($bytes / 1024, 2) . ' KB';
    } else {
        return $bytes . ' bytes';
    }
}

// S3 파일 삭제
function deleteFile($file_path) {
    try {
        // S3 URL에서 S3 키 추출
        if (strpos($file_path, 's3.amazonaws.com') !== false || strpos($file_path, 's3.') !== false) {
            // S3 URL에서 키 추출
            $parsed_url = parse_url($file_path);
            $s3_key = ltrim($parsed_url['path'], '/');
            
            $s3Manager = new S3FileManager();
            return $s3Manager->deleteFile($s3_key);
        }
        return true;
    } catch (Exception $e) {
        error_log("S3 파일 삭제 실패: " . $e->getMessage());
        return false;
    }
}

// 게시글 파일들 삭제
function deletePostFiles($pdo, $post_id) {
    try {
        // 이미지 삭제
        $stmt = $pdo->prepare("SELECT file_path FROM images WHERE post_id = ?");
        $stmt->execute([$post_id]);
        while ($row = $stmt->fetch()) {
            deleteFile($row['file_path']);
        }
        
        // 첨부파일 삭제
        $stmt = $pdo->prepare("SELECT file_path FROM files WHERE post_id = ?");
        $stmt->execute([$post_id]);
        while ($row = $stmt->fetch()) {
            deleteFile($row['file_path']);
        }
    } catch (Exception $e) {
        error_log("게시글 파일 삭제 중 오류: " . $e->getMessage());
    }
}

// 이미지 리사이징 (S3용 - 선택사항)
function resizeImageFromS3($s3_url, $max_width = 1200, $max_height = 800) {
    // S3에서 이미지를 다운로드하여 리사이징 후 다시 업로드
    // 필요시 구현
    return true;
}

// S3 Signed URL 생성 (비공개 파일용)
function getSignedUrl($file_path, $expiration = '+20 minutes') {
    try {
        if (strpos($file_path, 's3.amazonaws.com') !== false || strpos($file_path, 's3.') !== false) {
            $parsed_url = parse_url($file_path);
            $s3_key = ltrim($parsed_url['path'], '/');
            
            $s3Manager = new S3FileManager();
            return $s3Manager->getSignedUrl($s3_key, $expiration);
        }
        return $file_path;
    } catch (Exception $e) {
        error_log("Signed URL 생성 실패: " . $e->getMessage());
        return $file_path;
    }
}

// 디버그 함수 (S3용)
function debugS3Upload($file) {
    error_log("=== S3 Upload Debug ===");
    error_log("File name: " . ($file['name'] ?? 'NULL'));
    error_log("File size: " . ($file['size'] ?? 'NULL'));
    error_log("File type: " . ($file['type'] ?? 'NULL'));
    error_log("File error: " . ($file['error'] ?? 'NULL'));
    error_log("S3 Bucket: " . ($_ENV['AWS_S3_BUCKET'] ?? 'NOT SET'));
    error_log("S3 Region: " . ($_ENV['AWS_S3_REGION'] ?? 'NOT SET'));
    
    return true;
}
?>