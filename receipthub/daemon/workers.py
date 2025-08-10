from __future__ import annotations
import asyncio
from typing import List
from receipthub.daemon.queue_mem import InMemoryQueue, Job

async def _printer_worker(name: str, queue: InMemoryQueue):
    try:
        while True:
            job: Job = await queue.get()  # blocks until a job is due
            print(f"[worker:{name}] job={job.job_id} type={job.type} source={job.source} run_at={int(job.run_at)}", flush=True)
            # Simulate quick processing
            await asyncio.sleep(0.1)
            queue.task_done()
    except asyncio.CancelledError:
        # Graceful shutdown
        raise

def start_workers(printer_names: list[str], queue: InMemoryQueue) -> List[asyncio.Task]:
    tasks: List[asyncio.Task] = []
    for name in printer_names:
        tasks.append(asyncio.create_task(_printer_worker(name, queue), name=f"worker:{name}"))
    return tasks

async def stop_workers(tasks: List[asyncio.Task]) -> None:
    for t in tasks:
        t.cancel()
    for t in tasks:
        try:
            await t
        except asyncio.CancelledError:
            pass
