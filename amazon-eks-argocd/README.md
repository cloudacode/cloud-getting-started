# EKS with ArgoCD Pipeline

__EKS로 컨테이너 환경 구성 및 ArgoCD 배포 환경 실습__

EKS로 대규모 컨테이너 운영 환경을 만들고 배포 관리툴(ArgoCD)을 설치해 관리 콘솔로 유연하게 서비스를 배포, 관리 효율화 

## 사전 준비 사항

### AWS CLI 설정

AWS CLI 설치: [관련 링크](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)

AWS CLI 초기 설정: [관련 링크](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)

!!! note 
    원활한 실습을 위해 IAM User 권한에 `AdministratorAccess` policy 부여

## Architecture
![Architecture](images/eks-argo-web.png)

## 1. EKS 구성 하기

### IAM user for EKS
EKS는 Root User로 생성/접속하는 것을 보안상 권고하지 않으며 EKS을 관리하기 위한 권한(Kubernetes RBAC authorization)을 EKS를 생성한 IAM 엔터티(user 혹은 role)로 부터 할당을 시키기 때문에 IAM user 혹은 role를 사용중이지 않다면 필수로 IAM 엔터티를 생성하고 EKS 생성 역할을 부여 해야한다. 

https://docs.aws.amazon.com/eks/latest/userguide/create-cluster.html

사용중인 IAM 엔터티(유저, Role)가 있다면 eksctl 권한이 있는지 검토. 원활한 실습을 위해 **AdministratorAccess** policy 부여

Otherwise, create a IAM user with eksctl minimum policies.
https://eksctl.io/usage/minimum-iam-policies/

현재 세션의 IAM 엔터티 확인 방법
```bash
$ aws sts get-caller-identity
```

### Install eksctl and kubectl

EKS 생성을 위해 eksctl을 설치 하고 추후 kubernetes 관리를 위해 kubectl도 사전에 설치 필요: [kubectl 설치(1.18)](https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/install-kubectl.html)

[eksctl 설치](https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/eksctl.html)


### Deploy EKS Cluster

EKS 환경 배포
(참고: 실습 비용 절감을 위해 SPOT 인스턴스 사용)

```
$ eksctl create cluster -f ./eks-cluster-config.yml
```
EKS Cluster 구성 완료 까지 약 15분 소요

만약 CLI로 하고 싶다면 다음과 같이 수행
```
eksctl create cluster \
--name cloud-eks-01 \
--version 1.18 \
--region ap-northeast-2 \
--zones=ap-northeast-2a,ap-northeast-2c \
--nodegroup-name cloud-eks-workers \
--nodes 1 \
--nodes-min 1 \
--nodes-max 3 \
--with-oidc \
--managed \
--alb-ingress-access \
--spot \
--instance-types=c4.large,c5.large
```

### EKS Cluster 접속 확인

정상적인 output
```
[✔]  all EKS cluster resources for "cloud-eks-01" have been created
[ℹ]  nodegroup "cloud-eks-workers" has 1 node(s)
[ℹ]  node "ip-192-168-27-236.ap-northeast-2.compute.internal" is ready
[ℹ]  waiting for at least 1 node(s) to become ready in "cloud-eks-workers"
[ℹ]  nodegroup "cloud-eks-workers" has 1 node(s)
[ℹ]  node "ip-192-168-27-236.ap-northeast-2.compute.internal" is ready
[ℹ]  kubectl command should work with "/Users/kcchang/.kube/config", try 'kubectl get nodes'
[✔]  EKS cluster "cloud-eks-01" in "ap-northeast-2" region is ready
```

kubectl을 통해 추가된 node 확인
```
➜  ✗ kubectl get nodes
NAME                                                STATUS   ROLES    AGE   VERSION
ip-192-168-27-236.ap-northeast-2.compute.internal   Ready    <none>   19m   v1.18.9-eks-d1db3c
```

## 2. Application 배포

### Database 배포

상위 디렉토리에 `cloud-db-manifest`로 이동

Deploy the contents of the deployment file:
```bash
kubectl apply -f mysql-deployment.yaml
```

Display information about the Deployment:
```bash
kubectl describe deployment mysql
```

Deploy the contents of the service file:
```bash
kubectl apply -f mysql-service.yaml
```

배포가 정상적으로 완료가 되면 Pod 정보를 찾을수 있다
```bash
kubectl get pods -l app=mysql
```

Output
```bash
NAME                     READY   STATUS    RESTARTS   AGE
mysql-6fd94cc949-d8lj7   1/1     Running   0          23s
```

### Flask APP 배포

상위 디렉토리에 `cloud-flask-manifest`로 이동

Deploy the contents of the deployment file:
```bash
kubectl apply -f flask-deployment.yaml
```

Display information about the Deployment:
```bash
kubectl describe deployment cloud-flask
```

Deploy the contents of the service file:
```bash
kubectl apply -f flask-service.yaml
```

배포가 정상적으로 완료가 되면 Pod 정보를 찾을수 있다
```bash
kubectl get pods -l app=cloud-flask
```

flask app의 경우는 Service 타입을 LB로 외부 노출을 시켰으므로 다음과 같이 LB Endpoint를 확인 가능
```bash
kubectl get svc cloud-flask-svc
```

Output
```bash
NAME              TYPE           CLUSTER-IP       EXTERNAL-IP                                                                   PORT(S)        AGE
cloud-flask-svc   LoadBalancer   10.100.211.215   acd2f9103b9564eb3ada544282a1dee3-566651492.ap-northeast-2.elb.amazonaws.com   80:31126/TCP   101s 
```

해당 LB endpoint로 접근 하여 확인 동작 확인
ex) http://acd2f9103b9564eb3ada544282a1dee3-566651492.ap-northeast-2.elb.amazonaws.com/user

## 3. ArgoCD 연동

### ArgoCD CLI 설치
https://argoproj.github.io/argo-cd/cli_installation/

### ArgoCD 설치
https://argoproj.github.io/argo-cd/getting_started/

```
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```
This will create a new namespace, `argocd`, where Argo CD services and application resources will live.

### ArgoCD CLI 설치

Download the latest Argo CD version from [https://github.com/argoproj/argo-cd/releases/latest](https://github.com/argoproj/argo-cd/releases/latest). 

More detailed installation instructions can be found via the [CLI installation documentation](https://github.com/argoproj/argo-cd/blob/master/docs/cli_installation.md).

### ArgoCD Server 접속
In order to access server via URL, need to expose the Argo CD API server. Change the argocd-server service type to `LoadBalancer`:

```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```
LB Endpoint를 노출 하더라도 도메인 등록 시간이 소요 되므로 브라우저를 통한 접근이 가능하기 까지는 약 5분 소요

Check the LB Endpoint

```bash
kubectl get -n argocd svc argocd-server    
NAME            TYPE           CLUSTER-IP       EXTERNAL-IP                                                                    PORT(S)                      AGE
argocd-server   LoadBalancer   10.100.143.242   a1521dde2ec114a4eb7fb04632cab058-1608723687.ap-northeast-2.elb.amazonaws.com   80:32511/TCP,443:31088/TCP   17m
```

Also available to get the external LB endpoint as a raw value:

```bash
kubectl get -n argocd svc argocd-server --output jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

초기 `admin` 패스워드 확인 
```bash
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-server -o name | cut -d'/' -f 2
```

브라우저를 통해 LB Endpoint 에 접속

!!! note
    SSL인증서 연동을 하지 않아 브라우저에서 사이트가 안전하지 않는다는 메시지가 발생하기 때문에 실습 때는 무시하고 진행한다.

![argocd-web](images/argo-web-console.png)


### ArgoCD를 통해 모니터링 App(Prometheus, Grafana) 배포

웹 콘솔에 접속후 __+ New App__ 클릭하여 신규 애플리케이션(Prometheus) 생성

- GENERAL
  - Application Name: prometheus
  - Project: default
  - Sync Policy: Manual
- SOURCE
  - Repo URL: https://prometheus-community.github.io/helm-charts `HELM`
  - Chart: prometheus `13.6.0`
- DESTINATION
  - Cluster URL: https://kubernetes.default.svc
  - Namespace: default

__Create__ 진행 후

화면을 새로고침 하면 다음과 같이 앱이 하나 등록 되어 Sync가 아직 되지 않은 OutOfSync 상태로 확인 된다. Sync 정책을 Manual 로 하였기 때문에 초기에 OutOfSync 상태는 정상 이다.

__SYNC__ 수행 후

레포지토리 URL 이 올바르게 되어 있다면 문제 없이 sync가 완료되고 상세 페이지 역시 아래처럼 확인 가능하다 
![argocd-app-synced](images/argo-prometheus-synced.png) 

다시 웹 콘솔에서 __+ New App__ 클릭하여 신규 애플리케이션(Grafana) 생성

- GENERAL
  - Application Name: grafana
  - Project: default
  - Sync Policy: Manual
- SOURCE
  - Repo URL: https://grafana.github.io/helm-charts `HELM`
  - Chart: prometheus `6.6.2`
- DESTINATION
  - Cluster URL: https://kubernetes.default.svc
  - Namespace: default

아래 HELM 변수값 탭에서 `service.type` 검색 후 값을 `LoadBalancer` 로 변경
![grafana-service-type](images/grafana-helm-servicetype.png)

__Create__ 와 __SYNC__ 수행 후 정상적으로 애플리케이션이 만들어졌다면 admin password를 조회

```bash
kubectl get secret --namespace default grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

Endpoint 확인을 위해 ArgoCD 화면에서 Grafana 선택후 상세페이지
__Service__(화면에서는 svc grafana)

를 선택하면 Hostnames 항목에 앱에 접속 가능한 LB URL이 생성 되었으며 웹 브라우져로 접속후 정상적으로 Grafana가 기동 되었는지 확인
![grafana-dashboard](images/grafana-dashboard.png)


### Monitoring Dashboard 구성  

왼쪽 텝 __+__ Import -> Upload Json File:
`kubernetes-cluster-prometheus_rev1.json` 업로드

Options
  - prometheus: `Promethesus`

아래처럼 리소스에 대한 모니터링 대쉬보드 확인
![K8S Dashboard](images/grafana-k8s-dashboard.png)


## Clean Up
실습 완료 후 비용 절약을 위해 실습한 EKS 리소스를 정리
```
eksctl delete cluster --region=ap-northeast-2 --name=<your eks cluster name>
```

## Trobleshooting - EKS
https://aws.amazon.com/premiumsupport/knowledge-center/amazon-eks-cluster-access/

https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/troubleshooting.html#unauthorized

## Reference
https://argoproj.github.io/argo-cd/getting_started
