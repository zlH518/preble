from transformers import AutoTokenizer
import random
import sys, os


# Add the parent directory of the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from multi_experiment_benchmark_utils import AllExperiments, ExperimentType, DefaultWorkload, ConfigurableMajorExperimentArgs

from benchmark_utils import RequestGroup
from benchmark_workload_gen import *
from sglang.srt.managers.router.model_runner import GPUConfig
from data_parallel_request_cache import DataParallelRuntimeSelectionPolicy, CustomPolicyType
import random
from multi_exp_configs.multi_exp_utils import *

model_name = "mistralai/Mistral-7B-v0.1"

"""sgalng baseline server runtime config
"""
sglang_server_args = {
    'log_prefix_hit': True,
    'mem_fraction_static': 0.5,
    'context_length': 4096,
    "enable_flashinfer": True,
    'schedule_heuristic': 'lpm',
}
# GPU Configuration
baseline_gpu_configs = [
    GPUConfig(gpu_id=0, url=None, use_ssh=False, runtime_args=sglang_server_args),
    GPUConfig(gpu_id=1, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=2, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=3, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=4, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=5, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=6, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=7, url=None, use_ssh=False, runtime_args=sglang_server_args),
]
# add_simulation_to_gpu_config(baseline_gpu_configs)

"""ours server runtime config
"""
ours_server_args = {
    'log_prefix_hit': True,
    'mem_fraction_static': 0.5,
    'context_length': 4096,
    "enable_flashinfer": True,
    'schedule_heuristic': 'fcfs-mpq',
    "chunk_prefill_budget": 512,
    'report_hit_ratio': True 
}
# GPU Configuration
ours_gpu_configs = [
    GPUConfig(gpu_id=0, url=None, use_ssh=False, runtime_args=ours_server_args),
    GPUConfig(gpu_id=1, url=None, use_ssh=False, runtime_args=ours_server_args),
    # GPUConfig(gpu_id=2, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=3, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=4, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=5, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=6, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=7, url=None, use_ssh=False, runtime_args=sglang_server_args),
]
add_simulation_to_gpu_config(ours_gpu_configs)

ours_server_args_lpm = {
    'log_prefix_hit': True,
    'mem_fraction_static': 0.5,
    'context_length': 4096,
    "enable_flashinfer": True,
    'schedule_heuristic': 'lpm',
    "chunk_prefill_budget": 512,
    'report_hit_ratio': True 
}
# GPU Configuration
ours_gpu_configs_lpm = [
    GPUConfig(gpu_id=0, url=None, use_ssh=False, runtime_args=ours_server_args_lpm),
    GPUConfig(gpu_id=1, url=None, use_ssh=False, runtime_args=ours_server_args_lpm),
    # GPUConfig(gpu_id=2, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=3, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=4, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=5, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=6, url=None, use_ssh=False, runtime_args=sglang_server_args),
    # GPUConfig(gpu_id=7, url=None, use_ssh=False, runtime_args=sglang_server_args),
]
add_simulation_to_gpu_config(ours_gpu_configs_lpm)

exp_time = float('inf')
configuration_to_test = [
    # scale_to_gpu([24, 168, 0.3], len(ours_gpu_configs) // 2),
    # scale_to_gpu([24, 281, 0.5], len(ours_gpu_configs) // 2),
    # scale_to_gpu([24, 393, 0.7], len(ours_gpu_configs) // 2),
    # scale_to_gpu([24, 561, 1.0], len(ours_gpu_configs) // 2),
    # scale_to_gpu([24, 673, 1.2], len(ours_gpu_configs) // 2),
    scale_to_gpu([200, 5000, 25], len(ours_gpu_configs) // 2),
]
policies_to_test = [
    (DataParallelRuntimeSelectionPolicy.ROUND_ROBIN, "", baseline_gpu_configs, 'baseline'),
    (DataParallelRuntimeSelectionPolicy.CUSTOM, CustomPolicyType.GlobalSchedulerTime, ours_gpu_configs_lpm, 'all_stuff_lpm'),
    (DataParallelRuntimeSelectionPolicy.CUSTOM, CustomPolicyType.GlobalSchedulerTime, ours_gpu_configs, 'all_stuff'),

]

def gen_workloads_for_virtualenv(configuration_to_test, policies_to_test):
    for configuration in configuration_to_test:
        num_prefix_patters, num_requests, request_rate = configuration
        dataloader, request_groups, send_out_times_list = create_virtualenv_dataset(
            configuration,
            model_name, 
            exp_time, 
            data_path='/mnt/data/ssd/dongming/stateful_llm_serving/multi_node/benchmarks/datasets/results_trace_updated_v2.json',
            load_dist=LoadDistribution.EVEN,  # this have no effect on virtualenv
        )
        for policy, custom_policy, server_configs, custom_policy_msg in policies_to_test: # assuming each policy has the exact same settings
            # print(server_configs)
            req_groups = [RequestGroup(requests=requests,
                                       request_rate=request_rate/len(request_groups),  # the overall request rate is divided by the number of request groups
                                       send_out_times=send_out_times,
                                       request_type=ExperimentType.sequential) \
                            for requests, send_out_times in zip(request_groups, send_out_times_list)]
            yield DefaultWorkload(
                    dataloader=dataloader,
                    policy=policy,
                    custom_policy=custom_policy,
                    custom_policy_msg = custom_policy_msg,
                    request_groups=req_groups,
                    # send_out_times=send_out_times,
                    num_prefix_patterns=num_prefix_patters,
                    random_ratio=0.0,
                    exp_time=exp_time,
                    request_rate=request_rate,
                    num_requests=num_requests,
                    server_configs=server_configs,
                )

workloads = gen_workloads_for_virtualenv(configuration_to_test, policies_to_test)
loogle_experiment = ConfigurableMajorExperimentArgs(
    log_file_path="e2e/8r_virtual_rich/exp_3.log",
    csv_log_path="e2e/8r_virtual_rich/exp_3.csv",
    # log_file_path="logs/debug_loogle_cp_2048/exp.log",
    # csv_log_path="logs/debug_loogle_cp_2048/exp.csv",
    simulate=False,
    model_path=model_name,
    workload_configs=workloads,
    experiment_type=ExperimentType.default,
    experiment_name="virtual_e2e"
)

exp_args = AllExperiments(
    [loogle_experiment]
)
