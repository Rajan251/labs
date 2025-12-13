# Service Mesh Setup

1. Install Istio:
   `istioctl install --set profile=demo -y`

2. Enable Injection:
   `kubectl label namespace default istio-injection=enabled`
