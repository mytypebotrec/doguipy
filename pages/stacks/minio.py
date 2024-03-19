import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from python_on_whales import docker
from slugify import slugify

from models.models import User

from .. import base
from . import fields


def deploy_minio(modal, default_id=None, default_image=None, default_name=None, default_domain=None, default_port=None, default_envs=None):
        
        if default_id:
            docker.container.stop(default_id)
            
            docker.container.remove(default_id)

        envs = {}

        try:
            for line in default_envs.strip().split("\n"):
                if line.split("=")[1].lower() == 'false' or line.split("=")[1].lower() == 'true':
                    envs[line.split("=")[0]] = 'false' if line.split("=")[1].lower() == 'false' else 'true'
                else:
                    envs[line.split("=")[0]] = line.split("=")[1]
                    
        except:
            pass


        ####################   minio Api   ####################        
        var_domain      = urlparse(default_domain).hostname
        var_default     = os.environ.get('DOMAIN_BASE')
        var_image       = default_image
        var_name        = slugify(default_name)
        var_entrypoint  = 'http'
        var_ssl         = True

        if var_entrypoint == 'http':
            if var_domain:
                var_host = "Host(`"+var_domain+"`)"
            else:
                var_host = "Host(`"+var_name+"."+var_default+"`)"
                var_domain = var_name+"."+var_default
                
        else:
            var_host    = "HostSNI(`*`)"
            
        if var_ssl:
            var_entry   = 'websecure'
        else:
            var_entry   = 'web'
            
        var_port        = default_port if default_port else 9000
        var_envs        = envs
        var_volumes     = [
            (var_name+"_minio_data","/bitnami/minio/data"),
            ]
        
        if var_entrypoint == 'http':
            if var_domain:
                var_host_2 = "Host(`login."+var_domain+"`)"
            else:
                var_host_2 = "Host(`login."+var_name+"."+var_default+"`)"
    
        created = docker.run(
            detach=True,
            image=var_image,
            name=var_name,
            command=["minio", "server", "/bitnami/minio/data","--address",":{}".format(var_port),"--console-address",":9001"],
            hostname=var_domain,
            domainname=var_domain,
            restart='always',
            labels={
                "traefik.enable":"true",
                
                "traefik."+var_entrypoint+".routers."+var_name+"_storage.rule":var_host,
                "traefik."+var_entrypoint+".routers."+var_name+"_storage.entrypoints":var_entry,
                "traefik."+var_entrypoint+".services."+var_name+"_storage.loadbalancer.server.port":var_port,
                "traefik."+var_entrypoint+".routers."+var_name+"_storage.tls.certresolver":"le",
                "traefik."+var_entrypoint+".routers."+var_name+"_storage.service":var_name+"_storage",
                
                "traefik."+var_entrypoint+".routers."+var_name+".rule":var_host_2,
                "traefik."+var_entrypoint+".routers."+var_name+".entrypoints":var_entry,
                "traefik."+var_entrypoint+".services."+var_name+".loadbalancer.server.port":9001,
                "traefik."+var_entrypoint+".routers."+var_name+".tls.certresolver":"le",
                "traefik."+var_entrypoint+".routers."+var_name+".service":var_name+"",
            },
            publish=[(var_port,var_port)],
            networks=['traefik_public'],
            envs=var_envs,
            volumes=var_volumes
        )

        modal.close()

        

@ui.page('/form/minio')
def form_minio() -> None:

    if not app.storage.user.get('authenticated', False):
        return RedirectResponse('/login')
    else:
        user = User.get_by_id(app.storage.user.get('id'))

    base.base()

    load_dotenv(override=False)

    default_image = 'bitnami/minio:latest'
    
    default_envs = """MINIO_ROOT_USER=minio_usuario
MINIO_ROOT_PASSWORD=minio_senha"""
        
    ui.query('textarea').style('line-height: 24px')

    ui.label('Formulário minio-API').classes('text-2xl').style('color:gray')
    
    container_fields = ui.row().classes('w-full')
    
    with container_fields:
        fields.get_fields(template_deploy='minio', default_image=default_image, default_envs=default_envs)