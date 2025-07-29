# Java 17 런타임 이미지
FROM bellsoft/liberica-openjdk-alpine:17

# 작업 디렉토리 설정
WORKDIR /app

# 빌드된 JAR 파일 복사 (GitHub Actions에서 빌드된 파일)
COPY target/*.jar app.jar

# 포트 노출
EXPOSE 8080

# 애플리케이션 실행
ENTRYPOINT ["java", "-jar", "/app/app.jar"] 