## 사용 환경 변수 안내

이 프로젝트는 **GitHub Actions**를 통한 배포 자동화 과정에서 아래와 같은 환경 변수를 사용합니다.

| 환경 변수                | 설명                                                        |
|-------------------------|------------------------------------------------------------|
| `AWS_ACCESS_KEY`        | 배포용 AWS 액세스 키 (예: github-actions-deploy-user)       |
| `AWS_SECRET_ACCESS_KEY` | 배포용 AWS 시크릿 액세스 키 (예: github-actions-deploy-user)|
| `AWS_REGION`            | 사용할 AWS 리전 (예: ap-northeast-2 등)                    |
| `ECR_REPOSITORY`        | Docker 이미지를 업로드할 AWS ECR 리포지토리  이름           |


## ToDo List   
- Error Fix : logout.php
- Error Fix : dashboard.php(최근에 내가 작성한 게시글 목록)     