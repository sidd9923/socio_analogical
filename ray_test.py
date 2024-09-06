import ray
# Initialize Ray
if ray.is_initialized():
    ray.shutdown()
ray.init()

ray.cluster_resources()
