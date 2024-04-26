import random
import warnings

import numpy as np

random.seed(10)
np.random.seed(10)

import os
import sys

# Add the parent directory of the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import datetime
import time

warnings.simplefilter(action="ignore", category=FutureWarning)

from multi_node_loader import MultiNodeLoader
from model_runtime_manager import RequestFuncOutput, ModelDetails
from benchmark_utils import BenchmarkMetrics, MajorExperimentArgs, WorkloadConfig
from benchmark_workload_gen import *
from data_parallel_request_cache import DataParallelRuntimeSelectionPolicy, CustomPolicyType
from metrics_based_scheduler import LongestPrefixMatchSelector, GlobalLongestPrefixMatch
from global_policy_lp import LPScheduler

import gc
import logging
from typing import Dict, List
import torch
from data_parallel_request_cache import (
    CustomPolicyType,
    DataParallelRuntimeSelectionPolicy,
)
from global_policy_lp import LPScheduler
from greedy_lp import GurobiGreedyLPScheduler
from metrics_based_scheduler import GlobalLongestPrefixMatch, LongestPrefixMatchSelector
from model_runtime_manager import ModelDetails, RequestFuncOutput
from multi_node_loader import MultiNodeLoader

from benchmark_utils import BenchmarkMetrics, MajorExperimentArgs, WorkloadConfig
from benchmark_workload_gen import *

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("filelock").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("paramiko").setLevel(logging.WARNING)

log = logging.getLogger(__name__)


def regist_selector(
    policy, custom_policy, model_details: ModelDetails, workload_config: WorkloadConfig, gpu_configs
):
    if policy == DataParallelRuntimeSelectionPolicy.CUSTOM:
        if custom_policy == CustomPolicyType.ORACLE:
            oracle = Oracle(
                num_nodes=len(model_details.runtimes),
                num_workloads=workload_config.num_prefix_patterns,
            )
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=oracle,
            )
        elif custom_policy == CustomPolicyType.ORACLE_HOT_COLD:
            oracle = OracleHotCold(
                num_nodes=len(model_details.runtimes),
                num_workloads=workload_config.num_prefix_patterns,
            )
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=oracle,
            )
        elif custom_policy == CustomPolicyType.TBORACLE:
            oracle = TBOracle(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=oracle,
            )
        elif custom_policy == CustomPolicyType.TBORACLE_B:
            oracle = TBOracleB(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=oracle,
            )
        elif custom_policy == CustomPolicyType.LPM:
            lpm = LongestPrefixMatchSelector(
                num_nodes=len(model_details.runtimes),
                runtimes=model_details.runtimes,
            )
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=lpm,
            )
        elif custom_policy == CustomPolicyType.LOOGLE_ORACLE:
            oracle = LoogleOracle(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=oracle,
            )
        elif custom_policy == CustomPolicyType.GLPM:
            glpm = GlobalLongestPrefixMatch(
                num_nodes=len(model_details.runtimes), model_name=model_name
            )
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=glpm,
            )
        elif custom_policy == CustomPolicyType.GREEDY_LP:
            greedy_lp = GurobiGreedyLPScheduler(num_nodes=len(model_details.runtimes), gpu_configs=gpu_configs)
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=greedy_lp,
            )
        elif custom_policy == CustomPolicyType.GREEDY_LP_OLD:
            from greedy_lp_old import GurobiGreedyLPSchedulerV1
            greedy_lp =  GurobiGreedyLPSchedulerV1(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=greedy_lp,
            )
        elif custom_policy == CustomPolicyType.BASIC_MEM_SCHEDULER:
            from basic_mem_scheduler import BasicMemScheduler
            mem_waste = BasicMemScheduler(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.BASIC_MEM_SCHEDULERV2:
            from basic_mem_scheduler import BasicMemSchedulerV2 
            mem_waste = BasicMemSchedulerV2(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.BASIC_MEM_SCHEDULERV2_5:
            from basic_mem_scheduler import BasicMemSchedulerLoadOnly 
            mem_waste = BasicMemSchedulerLoadOnly(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.BasicMemSchedulerV3:
            from basic_mem_scheduler import BasicMemSchedulerV3 
            mem_waste = BasicMemSchedulerV3(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.HistogramBasedMemoryLoadScheduler:
            from histogram_based_scheduling import HistogramBasedMemoryLoadScheduler
            mem_waste = HistogramBasedMemoryLoadScheduler(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.HiostgramBasedRecompLoad:
            from histogram_based_scheduling import HistogramBasedRecomp
            mem_waste = HistogramBasedRecomp(num_nodes=len(model_details.runtimes), enable_eviction=False)
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.HiostgramBasedRecompLoadWithEviction:
            from histogram_based_scheduling import HistogramBasedRecomp
            mem_waste = HistogramBasedRecomp(num_nodes=len(model_details.runtimes), enable_eviction=True)
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.MemSchedulerEvictBasedOnLoad:
            from mem_scheduler_evict_based_on_load import MemSchedulerEvictBasedOnLoad
            mem_waste = MemSchedulerEvictBasedOnLoad(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.MemSchedulerWithGlobalEviction:
            from mem_scheduler_evict_based_on_load_with_global import MemSchedulerWithGlobalEviction
            mem_waste = MemSchedulerWithGlobalEviction(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.HiostgramBasedRecompLoadWithEvictionV2:
            from histogram_based_scheduling_v2 import HistogramBasedRecompV2
            mem_waste = HistogramBasedRecompV2(num_nodes=len(model_details.runtimes), enable_eviction=True)
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=mem_waste,
            )
        elif custom_policy == CustomPolicyType.TB_DOMAIN_ORACLE:
            oracle = TBMultiDomainOracle(num_nodes=len(model_details.runtimes))
            model_details.update_runtime_selection_policy(
                DataParallelRuntimeSelectionPolicy.CUSTOM,
                custom_runtime_selector=oracle,
            )
    else:
        model_details.update_runtime_selection_policy(policy, None)


def load_and_run_benchmark(
    model_details: ModelDetails,
    workload_config: WorkloadConfig,
    policy,
    custom_policy=None,
    custom_msg="",
    gpu_configs=None
):
    num_workloads = workload_config.num_prefix_patterns
    distribution_of_non_shared = workload_config.random_ratio
    num_requests = workload_config.num_requests
    rps = workload_config.request_rate
    exp_time = workload_config.exp_time
    requests = workload_config.requests
    tokenizer = workload_config.dataloader.tokenizer

    logging.info(
        f"=====STARTING Policy {policy}-{custom_policy}:{custom_msg}, {num_workloads} WORKLOADS, {distribution_of_non_shared} NON-SHARED, {num_requests} REQUESTS, {rps} REQ/s, {exp_time} seconds ====="
    )
    regist_selector(policy, custom_policy, model_details, workload_config,gpu_configs=gpu_configs)

    tic_benchmark = time.time()
    results: List[RequestFuncOutput] = model_details.get_experiment_results(
        requests, rps, exp_time, workload_config.send_out_times
    )
    overall_latency = time.time() - tic_benchmark

    counts = model_details.request_router.get_model_selection_counts()
    exp_params = f"{model_name}, {num_workloads}, {distribution_of_non_shared}, {num_requests}, {rps}, {policy}-{custom_policy}:{custom_msg}, {exp_time}"
    detail_log_path = directory + '/' + exp_params.replace(", ", "_").replace("/", "-") + '.json'
    if custom_policy == CustomPolicyType.BASIC_MEM_SCHEDULER:
        model_details.request_router.custom_selector.print()

    bench_metrics = BenchmarkMetrics.gen_benchmark_metrics(
        tokenizer=tokenizer,
        req_func_outputs=results,
        overall_latency=overall_latency,
        time_limit=exp_time,
        gpu_counts=counts,
        detail_log_path=detail_log_path,
    )
    bench_metrics.to_log_file(exp_params)


def test_oracle_random_basic(exp_args: MajorExperimentArgs):
    loader = MultiNodeLoader(exp_args.simulate)
    gpu_configs = exp_args.gpu_configs
    for workload_config in exp_args.workload_configs:
        logging.info(workload_config)
        logging.info(
            f"Using load distribution of {workload_config.dataloader.load_dist}"
        )
        # dataloader = RandomDataLoader(num_workloads, num_requests, tokenizer, LoadDistribution.EVEN, distribution_of_non_shared, 1)
        for selector_config in exp_args.selector_configs:
            model_details = loader.load_model(
                **exp_args.runtime_args
            )  # TODO: clear cache instead of reload
            policy, custom_policy, custom_msg = selector_config
            load_and_run_benchmark(model_details, workload_config, policy, custom_policy, custom_msg, gpu_configs=gpu_configs)
            if custom_policy == CustomPolicyType.GREEDY_LP:
                lp_scheduler: GurobiGreedyLPScheduler = model_details.request_router.custom_selector
                lp_scheduler.lp_tree_traversal.pretty_print(lp_scheduler.tree_cache.root_node, depth_limit=4)
            loader.unload_model(model_details)
            torch.cuda.empty_cache()
            gc.collect()
            time.sleep(10)
            import statistics
            print(statistics.mean(model_details.scheduling_overheads))
            print(statistics.median(model_details.scheduling_overheads))
            print(statistics.stdev(model_details.scheduling_overheads))
            print(model_details.num_iters)
            exit(0)


if __name__ == "__main__":
    # from benchmarks.exp_configs.react_simulator_config_toolbench import exp_args
    # from benchmarks.exp_configs.react_simulator_config import exp_args
    # from benchmarks.exp_configs.react_mixed_config import exp_args
    from benchmarks.exp_configs.react_simulator_config_loogle import exp_args
    directory = os.path.dirname(exp_args.log_file_path)
    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    logging.basicConfig(level=logging.INFO, filename=exp_args.log_file_path)
    formatter = logging.Formatter('%(filename)s:%(lineno)d - %(levelname)s - %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    # Add current time to log file
    start_date = datetime.datetime.utcnow()
    start_time = time.time()
    logging.info(f"Starting Experiment at {start_date}")
    # model_name = "mistralai/Mistral-7B-v0.1"
    # model_name = "lmsys/vicuna-13b-v1.5"
    model_name = exp_args.runtime_args["model_path"]
    logging.info(f"Model Name: {model_name}")

    test_oracle_random_basic(exp_args)
    logging.info(f"Total Experiment Time: {time.time() - start_time}")
