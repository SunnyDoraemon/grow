# 使用kubeadm工具安装kubernetes

本文以Kubernetes v1.30为例，讲述如何通过kubeadm工具部署一个符合k8s最佳实践的最小化集群。

## 一、准备工作
- 准备一台CPU2核心及以上，2GB或更多RAM的Linux主机。
    - Kubernetes项目为机遇Debian和Red Had的Linux发行版以及一些不提供包管理器的发行版提供通用指令。
- 集群中所有机器网络彼此能互通。
- 所有机器不可以有重复的`hostname`、`MAC地址`或`product_uuid`

### 1.1 关闭swap分区
> swap分区是Linux系统中用于扩展物理内存的一种机制。<br>
> 在物理内存耗尽时，系统可以将部分数据暂时存储到硬盘上的Swap空间。然而，在某些性能敏感的应用场景，使用Swap交换分区可能导致一些不可预测的延迟。所以，完全关闭Swap可以帮助保持性能的一致性。

```bash 
sudo swapoff -a # 临时关闭
sudo sed -i.bak '/swap/s/^/#/' /etc/fstab # 永久关闭
```

### 1.2 安装容器运行时
Kubernetes为了在Pod中运行容器，使用[容器运行时](https://kubernetes.io/zh-cn/docs/setup/production-environment/container-runtimes/)(Container Runtime)。

默认情况下 Kubernetes使用[容器运行时接口](https://kubernetes.io/zh-cn/docs/concepts/overview/components/#container-runtime)(Container Runtime Inerface, CRI)来与你选择的容器运行时进行交互。

> 如果不指定容器运行时，kubeadm会自动扫描已知的endpoints列表来检测已安装的容器运行时。<br>
> 如果检测到有多个或者没有容器运行时，kubeadm会抛出一个错误并要求你指定一个想要使用的运行时。

&emsp;Kubernetes早期仅适用于特定的容器运行时:`Docker Engine`。后来增加了对其他容器运行时的支持。支持CRI标准，让Kubernetes和多种不同运行时之间交互操作有了标准接口。但是Docker Engine没有实现CRI，因此Kubernetes项目保留了一个特殊实现:`dockershim`来帮助过渡，并使dockershim代码成为了kubernetes的一部分。<br>

&emsp;从v1.24版本起，Kubernetes已经从项目中移除了Dockershim代码，默认已经不再支持Docker Engine；但是`Mirantis`公司实现了一个Dockershim的第三方代替品[cri-dockerd](https://github.com/Mirantis/cri-dockerd),其允许Kubernetes通过CRI来使用Docker Engine,但是需要额外安装该服务。

本文选择`Containerd`作为Kubernetes的容器运行时。此处不赘述其部署和配置过程。
> 如果你的文件系统是xfs，并且ftype=0则不支持overlay2，会导致containerd启动失败，<后续所有操作都无济于事。相关报错如下所示:<br>
```bash
could not use snapshotter overlayfs in metadata plugin  error="/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs does not support d_type. If the backing filesystem is xfs, please reformat with ftype=1 to enable d_type support"
```

```bash
# 假如你机器没有Containerd，又不想搜怎么装，看下面
yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
yum install containerd -y
systemctl enable --now containerd
systemctl status containerd
```

相关参考:
- [FAQ: What’s the deal with dockershim and cri-dockerd?](https://www.mirantis.com/blog/cri-dockerd-faq-blog)
- [Container Runtime Interface (CRI): Past, Present, and Future](https://www.aquasec.com/cloud-native-academy/container-security/container-runtime-interface/)

## 二、master机器相关部署
### 2.1 安装 kubeadm、kubelet和kubectl
需要在每台机器上安装
- `kubeadm`：用来初始化集群的工具
- `kubelet`：在集群中的每个节点上用来启动Pod和容器的管理端工具
- `kubectl`：用来与集群进行通信交互的命令行工具

> Kubeadm不能协助安装`kubelet`或`kubectl`,所以要确保`kubelet和kubectl`与通过kubeadm安装的`控制平面`的版本相匹配，避免版本偏差带来的预料之外的错误和问题而导致的一些风险。<br>
> 控制平面和kubelet之间可以存在一个次要版本的偏差，但是kubelet的版本不可以超过API服务器的版本；例如，1.7.0的kubelet可以完全兼容1.8.0的API服务器，反之则不可以。

*[Kubernetes版本与版本间的偏差策略](https://kubernetes.io/zh-cn/releases/version-skew-policy/)* <br>
*[kubeadm特定的版本偏差策略](https://kubernetes.io/zh-cn/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/#version-skew-policy)*

#### 2.1.1 禁用SELinux

[参考文档](https://docs.redhat.com/zh_hans/documentation/red_hat_enterprise_linux/7/html/selinux_users_and_administrators_guide/sect-security-enhanced_linux-introduction-selinux_modes)

禁用SELinux时允许容器访问主机文件系统所必须的。
``` bash
# 将 SELinux 设置为 permissive 模式（相当于将其禁用）
sudo setenforce 0
sudo sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config
```


#### 2.1.2 配置yum仓库
`exclude `参数确保了和Kubernetes相关的软件包在运行`yum update`时不会被升级，省委升级Kubernetes需要遵循特定的过程。
```toml
# 将以下内容写入 /etc/yum.repos.d/kubernetes.repo文件

# 这是Kubernetes官方源,由于山高路远问题，将enabled设置为了0(如果你有https_proxy则可以直接使用官方源)
[kubernetes-io]
name=Kubernetes-v1.30 k8s.io
baseurl=https://pkgs.k8s.io/core:/stable:/v1.30/rpm/
enabled=0
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.30/rpm/repodata/repomd.xml.key
exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni

[kubernetes-aliyun]
name=Kubernetes-v1.30 aliyun
baseurl=https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.30/rpm/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.30/rpm/repodata/repomd.xml.key
exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni
```
将yum repo写入配置
```bash
# 此操作会覆盖 /etc/yum.repos.d/kubernetes.repo 中现存的所有配置
cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
[centos-custom-base]
name=CentOS-\$releasever - Base
baseurl=http://mirrors.ustc.edu.cn/centos-vault/centos/\$releasever/os/\$basearch/
enabled=1
gpgcheck=0

[centos-custom-updates]
name=CentOS-\$releasever - Updates
baseurl=http://mirrors.ustc.edu.cn/centos-vault/centos/\$releasever/updates/\$basearch/
enabled=1
gpgcheck=0

[centos-custom-extras]
name=CentOS-\$releasever - Extras
baseurl=http://mirrors.ustc.edu.cn/centos-vault/centos/\$releasever/extras/\$basearch/
enabled=1
gpgcheck=0

[centos-custom-epel]
name=Extra Packages for Enterprise Linux 7 - \$basearch
baseurl=https://mirrors.aliyun.com/epel/7/\$basearch/
failovermethod=priority
enabled=1
gpgcheck=0

[kubernetes-io]
name=Kubernetes-v1.30 k8s.io
baseurl=https://pkgs.k8s.io/core:/stable:/v1.30/rpm/
enabled=0
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.30/rpm/repodata/repomd.xml.key
exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni

[kubernetes-aliyun]
name=Kubernetes-v1.30 aliyun
baseurl=https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.30/rpm/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.30/rpm/repodata/repomd.xml.key
exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni
EOF
```
运行以下命令生成缓存<br>
`yum clean all && yum makecache` 

#### 2.1.3 安装和启用
**安装相关工具**<br>
`sudo yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes-aliyun`
> ps:由于repo配置了`exclude`防止`yum update`导致工具升级，所以此处也指定了`disableexcludes`

**启用kubelet**<br>
`sudo systemctl enable --now kubelet`

### 2.2 配置cgroup驱动程序

容器运行时和kubelet都有[cgroup driver](https://kubernetes.io/zh-cn/docs/setup/production-environment/container-runtimes/#cgroup-drivers)属性,需要保证`kubelet`和`容器运行时`使用的是相同的cgroup驱动，否则kubelet进程会运行失败。

```bash
#kubelet的cgroup driver配置在【2.3初始化集群】的kubeadm-init-config.yaml中有体现

#containerd相关配置如下：

# 备份原containerd配置文件
mv /etc/containerd/config.toml /etc/containerd/config.tomlbk
# 将默认配置导出成新的config.toml
containerd config default > /etc/containerd/config.toml
# 修改cgroup driver
sed -i 's/SystemdCgroup\ \=\ false/SystemdCgroup\ \=\ true/g' /etc/containerd/config.toml
# 修改sandbox 镜像为阿里云镜像
sed -i 's/registry.k8s.io/registry.aliyuncs.com\/google_containers/g' /etc/containerd/config.toml
#重启containerd
systemctl restart containerd
# runtime-endpoint指定（不指定的话，crictl images就可以看到相关Warning）
crictl config runtime-endpoint unix:///var/run/containerd/containerd.sock
```


### 2.3 初始化集群

[参考文档](https://kubernetes.io/zh-cn/docs/reference/config-api/kubeadm-config.v1beta3/)
```bash
# 写入hosts
# 由于我的示例机器ip为10.10.5.175，所以特此配置
# 下文所有10.10.5.175均应该改成你的机器ip，hosts名称也是一样
echo "10.10.5.175 kube-node-175 vm-server-175" >> /etc/hosts

```

将以下内容写入配置文件
> 注意！！！，把`10.10.5.175`和`kube-node-175`改成你自己机器的地址

`vim /etc/kubernetes/kubeadm-init-config.yaml`
```yaml
apiVersion: kubeadm.k8s.io/v1beta3
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: abcdef.0123456789abcdef
  ttl: 24h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 10.10.5.175
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///var/run/containerd/containerd.sock
  imagePullPolicy: IfNotPresent
  name: kube-node-175
  taints: null
---
apiServer:
  timeoutForControlPlane: 4m0s
apiVersion: kubeadm.k8s.io/v1beta3
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controllerManager: {}
dns: {}
etcd:
  local:
    imageRepository: registry.aliyuncs.com/google_containers
    dataDir: /var/lib/etcd
imageRepository: registry.aliyuncs.com/google_containers
kind: ClusterConfiguration
kubernetesVersion: 1.30.3
networking:
  dnsDomain: cluster.local
  podSubnet: 10.244.0.0/16
  serviceSubnet: 10.96.0.0/12
scheduler: {}
---
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
cgroupDriver: systemd
```
执行初始化命令<br>
`kubeadm init --config /etc/kubernetes/kubeadm-init-config.yaml`

将生成的kubectl配置文件放至相应位置
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```
#### 2.3.1 记住这个配置
```bash
# 这是初始化输出日志末尾的信息，后续往集群加入节点需要使用这一句命令
kubeadm join 10.10.5.175:6443 --token abcdef.0123456789abcdef \
	--discovery-token-ca-cert-hash sha256:54c153e1a7ecd36014976d982f2926559fd25c95cadd327212abeccac3d319d6

```

#### 2.3.2 状态查看
 此时kubeadm初始化就算完成了，下面可以使用`kubectl get all -A`来查看一下集群基础服务状态,显示如下
 ```
 $ kubectl get all -A
NAMESPACE     NAME                                        READY   STATUS    RESTARTS   AGE
kube-system   pod/coredns-7b5944fdcf-5jcqb                0/1     Pending   0          29s
kube-system   pod/coredns-7b5944fdcf-dqsks                0/1     Pending   0          29s
kube-system   pod/etcd-kube-node-175                      1/1     Running   0          45s
kube-system   pod/kube-apiserver-kube-node-175            1/1     Running   0          44s
kube-system   pod/kube-controller-manager-kube-node-175   1/1     Running   0          44s
kube-system   pod/kube-proxy-v44vr                        1/1     Running   0          29s
kube-system   pod/kube-scheduler-kube-node-175            1/1     Running   0          44s

NAMESPACE     NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
default       service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP                  45s
kube-system   service/kube-dns     ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   44s

NAMESPACE     NAME                        DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
kube-system   daemonset.apps/kube-proxy   1         1         1       1            1           kubernetes.io/os=linux   44s

NAMESPACE     NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
kube-system   deployment.apps/coredns   0/2     2            0           44s

NAMESPACE     NAME                                 DESIRED   CURRENT   READY   AGE
kube-system   replicaset.apps/coredns-7b5944fdcf   2         2         0       29s
 ```
`ps:coredns 显示Pending是由于，目前集群还确实CNI组件
不仅coredns处于pending，kubelet此时也会提示CNI尚未准备好`


BTW:
```bash
# 这是用变量初始化的一种方式，此处不使用！！！
# kubeadm init \
#   --apiserver-advertise-address=10.10.5.175 \
#   --image-repository registry.aliyuncs.com/google_containers \
#   --kubernetes-version v1.30.3 \
#   --service-cidr=10.96.0.0/12 \
#   --pod-network-cidr=10.244.0.0/16
```

### 2.4 安装CNI组件

```bash
# 下载flannel yaml
wget -O /etc/kubernetes/kube-flannel.yml https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
# 修改镜像地址（山高路远原因）（这个站点不一定长期有效，如失效请自行寻找其他镜像）
sed -i 's/docker.io/swr.cn-north-4.myhuaweicloud.com\/ddn-k8s\/docker.io/g' /etc/kubernetes/kube-flannel.yml
# 部署flannel
kubectl apply -f /etc/kubernetes/kube-flannel.yml

# 如果你docker配置了加速，那你也可以这么干...
# docker pull flannel/flannel-cni-plugin:v1.5.1-flannel1
# docker save -o flannel-cni-plugin.tar flannel/flannel-cni-plugin:v1.5.1-flannel1
# ctr -n k8s.io images import flannel-cni-plugin.tar

# docker pull flannel/flannel:v0.25.5
# docker save -o flannel.tar flannel/flannel:v0.25.5
# ctr -n k8s.io images import flannel.tar
```

### 2.5 小结

至此，master节点的相关操作就已经完成了,如果你不需要其他工作节点的话，移除`NoSchedule`污点，这个集群就可以部署负载了。

```bash
#你可以部署一个nginx，并使用端口转发将服务映射到机器端口上去

# nginx部署
kubectl create deployment nginx --image=daocloud.io/nginx:latest
#此时你会发现服务一直pending，是因为默认情况下，出于安全原因，你的集群不会在控制平面节点上调度 Pod。 如果你希望能够在单机 Kubernetes 集群等控制平面节点上调度 Pod，请运行:
kubectl taint nodes --all node-role.kubernetes.io/control-plane-

#svc初始化
kubectl expose deployment nginx --port=80 --type=NodePort
# 端口映射
kubectl port-forward svc/nginx --address 0.0.0.0 80:80

访问nginx
http://10.10.5.175
```

## 三、worker部署

在worker节点上重复执行
- [1.1 关闭swap分区](#11-关闭swap分区)
- [1.2 安装容器运行时](#12-安装容器运行时)
- [2.1 安装 kubeadmkubelet和kubectl](#21-安装-kubeadmkubelet和kubectl)
- [2.2 配置cgroup驱动程序](#22-配置cgroup驱动程序)


**将节点加入集群**

[看这里](#231-记住这个配置)

其中`10.10.5.175:6443`、`--token`、`--discovery-token-ca-cert-hash`改成你自己相关的信息

```bash
# token 24小时过期
# 如果你看不到上面kubeadm init的输出信息了，不要慌

# 查看token
kubeadm token list

# 如果token过期了，重新创建
kubeadm token create

# 不知道--discovery-token-ca-cert-hash的值，没关系，通过openssl相关命令来获取它
# 如果你没有openssl命令，请自行搜索安装...
# 下面是一句命令分成了多行，请你千万别分成两次执行！！！
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | \
   openssl dgst -sha256 -hex | sed 's/^.* //'

# 上面你就获取到了--discovery-token-ca-cert-hash的值，下面你就可以按照2.3.1的方式去join这个节点了
# 请注意，上面获取token和cert值的命令是在master节点上执行

# kubeadm join命令是在worker节点上执行 (XX换成你自己的信息)
kubeadm join XX.XX.XX.XX:6443 --token XX \
	--discovery-token-ca-cert-hash XX

```

至此，不出意外的话，你的worker节点就初始化并加入集群成功了
`kubectl get nodes` 查看一下吧

更多子节点的加入过程同上即可。


这样，一个基于`kubeadm`搭建，符合k8s最佳实践的单master多worker的集群就搭建完成了。


至于，`高可用集群`、`storage`、`ingress`等，后续将由其他文章介绍，未完待续...

