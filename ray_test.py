import ray
# Initialize Ray
if ray.is_initialized():
    ray.shutdown()
ray.init(ignore_reinit_error=True)

ray.cluster_resources()
