from src.utils.task import TaskContext, create_task_chain

import argparse


def main():
    parser = argparse.ArgumentParser(description="Run tasks with a specific configuration")
    parser.add_argument('--config', '-c', type=str, required=False, default='config.yaml',
                        help="Path to the configuration file (default: config.yaml)")
    args = parser.parse_args()

    context = TaskContext(config_path=args.config)  # 创建任务上下文
    tasks_list = list(context.config.tasks.keys())
    task_chain = create_task_chain(task_types=tasks_list, context=context)
    task_chain.execute(context)


if __name__ == "__main__":
    main()