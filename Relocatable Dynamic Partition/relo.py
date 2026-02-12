import os
import sys

# ============================================
# MEMORY ALLOCATION ACTIVITY (FCFS)

# ============================================

class Job:
    def __init__(self, name, size, tat):
        self.name = name
        self.size = size
        self.tat = tat
        self.remaining = tat


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def pause(message):
    input(f"\n{message}")


def display_memory(memory):
    print("\nMEMORY STRUCTURE")
    print("+------------+------------+------------+")
    print("|   START    |    END     |   STATUS   |")
    print("+------------+------------+------------+")

    for block in memory:
        print("| {:^10} | {:^10} | {:^10} |".format(
            block['start'],
            block['end'],
            block['status']
        ))

    print("+------------+------------+------------+")


def display_job_list(jobs):
    print("\nJOB LIST")
    print("+------------+------------+------------+")
    print("|    JOB     |    SIZE    |    TAT     |")
    print("+------------+------------+------------+")

    for job in jobs:
        print("| {:^10} | {:^10} | {:^10} |".format(
            job.name,
            job.size,
            job.tat
        ))

    print("+------------+------------+------------+")


def compact_memory(memory):
    print("\n>>> Compaction is performed...")
    pause("Press Enter to continue...")

    new_memory = []
    current_start = 0
    total_end = memory[-1]['end']

    for block in memory:
        if block['status'] != "FREE":
            size = block['end'] - block['start']
            new_memory.append({
                'start': current_start,
                'end': current_start + size,
                'status': block['status']
            })
            current_start += size

    if current_start < total_end:
        new_memory.append({
            'start': current_start,
            'end': total_end,
            'status': "FREE"
        })

    return new_memory


# ================= MAIN PROGRAM =================

clear()

print("===========================================")
print("ML-M3: ACT3 - Relocatable Dynamic Partition")
print("Programmed by: Palacios Ryan Paul J.")
print("===========================================")

try:
    memory_size = int(input("Enter Memory Size (M): "))
    os_size = int(input("Enter OS Size (M): "))

    if os_size >= memory_size:
        print("Error: OS size must be smaller than Memory size.")
        sys.exit()

    num_jobs = int(input("Enter Number of Jobs: "))

except ValueError:
    print("Invalid input! Numbers only.")
    sys.exit()

jobs = []

for i in range(num_jobs):
    try:
        size = int(input(f"Enter size of Job {i+1}: "))
        tat = int(input(f"Enter TAT of Job {i+1}: "))
        jobs.append(Job(f"Job{i+1}", size, tat))
    except ValueError:
        print("Invalid input!")
        sys.exit()

display_job_list(jobs)

memory = [
    {'start': 0, 'end': os_size, 'status': "OS"},
    {'start': os_size, 'end': memory_size, 'status': "FREE"}
]

waiting_queue = jobs.copy()
running_jobs = []

display_memory(memory)
pause("Press Enter to start simulation...")

# ================= SIMULATION =================

while waiting_queue or running_jobs:

    # ----------- TIME UPDATE FIRST -----------
    for job in running_jobs:
        job.remaining -= 1

    # ----------- STRICT FCFS DEALLOCATION -----------
    while running_jobs and running_jobs[0].remaining <= 0:

        job = running_jobs[0]  # always first job only

        print(f"\n>>> {job.name} finished. Deallocating...")
        pause("Press Enter to continue Deallocation...")

        for block in memory:
            if block['status'] == job.name:
                block['status'] = "FREE"

        running_jobs.pop(0)  # remove first only

        display_memory(memory)
        pause("Press Enter to proceed...")

    # ----------- ALLOCATION (FCFS) -----------
    for job in waiting_queue[:]:
        allocated = False

        for i, block in enumerate(memory):
            if block['status'] == "FREE":
                block_size = block['end'] - block['start']

                if block_size >= job.size:
                    print(f"\n>>> Allocating {job.name}")
                    pause("Press Enter to continue Allocation...")

                    new_block = {
                        'start': block['start'],
                        'end': block['start'] + job.size,
                        'status': job.name
                    }

                    memory.insert(i, new_block)
                    block['start'] += job.size

                    if block['start'] == block['end']:
                        memory.remove(block)

                    running_jobs.append(job)
                    waiting_queue.remove(job)

                    display_memory(memory)
                    pause("Press Enter to continue...")
                    allocated = True
                    break

        if not allocated and waiting_queue:
            print(f"\n>>> Not enough contiguous space for {waiting_queue[0].name}.")
            memory = compact_memory(memory)
            display_memory(memory)
            pause("Press Enter to continue...")
            break  # FCFS basis

print("\nAll jobs completed.")
print("Program terminated successfully.")
