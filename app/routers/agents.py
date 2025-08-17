import os
import paramiko
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Form, Request, Depends
from sqlalchemy.exc import SQLAlchemyError
from ..db import get_session
from ..models import Agent
from ..security import require_basic

router = APIRouter()

MANAGER_SECRET = os.getenv("MANAGER_SECRET", "")

@router.post("/agents/register")
async def register_agent(
    request: Request,
    x_manager_secret: Optional[str] = Header(None, convert_underscores=False)
):
    if not MANAGER_SECRET or x_manager_secret != MANAGER_SECRET:
        raise HTTPException(status_code=401, detail="Bad secret")

    data = await request.json()
    name = data.get("agent_name") or data.get("name") or "agent"
    wallet = data.get("wallet_address")
    host = data.get("host")
    version = data.get("version")

    try:
        with get_session() as session:
            # Upsert by name
            agent = session.query(Agent).filter(Agent.name == name).first()
            if not agent:
                agent = Agent(name=name)
            agent.wallet = wallet
            agent.host = host
            agent.version = version
            agent.last_seen = datetime.utcnow()
            session.add(agent)
            session.commit()
        return {"ok": True}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/deploy")
async def deploy_agent(
    _: bool = Depends(require_basic),
    host: str = Form(...),
    ssh_user: str = Form("root"),
    ssh_pass: str = Form(""),
    wallet_address: str = Form(""),
    agent_name: str = Form("")
):
    # Very simple SSH deploy using Paramiko + git + docker compose
    AGENT_REPO_URL = os.getenv("AGENT_REPO_URL", "https://github.com/evdokimenkoiv/MysteriumNET-Agent.git")
    manager_url = os.getenv("MANAGER_URL_EXTERNAL", "") or os.getenv("MANAGER_URL", "")
    if not manager_url:
        # Best-effort default: try http://<manager-ip>:8080
        manager_port = os.getenv("MANAGER_PORT", "8080")
        manager_ip = "127.0.0.1"
        manager_url = f"http://{manager_ip}:{manager_port}"

    secret = os.getenv("MANAGER_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="MANAGER_SECRET is not set")

    # Build remote commands
    remote_cmd = f'''set -e
export DEBIAN_FRONTEND=noninteractive
if ! command -v docker >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y ca-certificates curl gnupg lsb-release git
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc || true
  chmod a+r /etc/apt/keyrings/docker.asc || true
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker || true
fi

mkdir -p /opt/mysterium
if [ ! -d /opt/mysterium/MysteriumNET-Agent/.git ]; then
  rm -rf /opt/mysterium/MysteriumNET-Agent || true
  git clone {AGENT_REPO_URL} /opt/mysterium/MysteriumNET-Agent
fi

cd /opt/mysterium/MysteriumNET-Agent
cat > .env <<EOF
MANAGER_URL={manager_url}
MANAGER_SECRET={secret}
WALLET_ADDRESS={wallet_address}
AGENT_NAME={agent_name}
EOF

docker compose -f docker-compose.standalone.yml up -d --build
'''
    # SSH
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=ssh_user, password=ssh_pass or None, timeout=30)
        _, stdout, stderr = client.exec_command(remote_cmd)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", "ignore")
        err = stderr.read().decode("utf-8", "ignore")
        client.close()
        if exit_status != 0:
            raise HTTPException(status_code=500, detail=f"Remote deploy failed: {err or out}")
        return {"ok": True, "host": host, "output": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH error: {e}")
