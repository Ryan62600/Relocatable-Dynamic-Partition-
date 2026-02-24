import os
import sys

# ============================================
# FORMATTING & COLORS
# ============================================
GREEN = '\033[92m'
RESET = '\033[0m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RED = '\033[91m'

class Job:
    def __init__(self, name, size, tat):
        self.name = name
        self.size = size
        self.tat = tat
        self.remaining = tat
        self.allocated = False

def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        print("\033[H\033[J", end="")

def compact_memory(memory):
    new_memory = []
    current_start = 0
    total_end = memory[-1]['end']

    for block in memory:
        if block['status'] != "Free":
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
            'status': "Free"
        })
    return new_memory

def display_combined_table(os_sz, memory, turn, deallocated_jobs, compacted):
    print("\n" + "="*85)
    title = f"{BOLD}RELOCATABLE DYNAMIC PARTITION (FCFS) - SET {turn}{RESET}"
    if compacted:
        title += f" {YELLOW}[COMPACTION PERFORMED]{RESET}"
    print(title.center(105))
    print("="*85)
    print(f"{'PARTITION':<12} | {'SIZE':<8} | {'ALLOCATION COLUMN':<25} | {'DEALLOCATION COLUMN':<25}")
    print("-" * 85)
    
    # OS Row
    print(f"{'OS Area':<12} | {f'{os_sz}K':<8} | {'SYSTEM OS':<25} | {'SYSTEM OS':<25}")
    
    # Dynamic Partitions
    p_num = 1
    for block in memory:
        if block['status'] == "OS":
            continue
            
        b_size = block['end'] - block['start']
        status = block['status']
        
        if status in deallocated_jobs:
            dealloc_val = f"{GREEN}Free (Cleared){RESET}"
            alloc_display = f"{GREEN}{status}{RESET}"
        elif status == "Free":
            dealloc_val = "Free"
            alloc_display = "Free"
        else:
            dealloc_val = status
            alloc_display = status

        print(f"{f'P{p_num}':<12} | {f'{b_size}K':<8} | {alloc_display:<34} | {dealloc_val:<34}")
        p_num += 1
    
    print("-" * 85)
    if deallocated_jobs:
        print(f"REMARKS: Jobs cleared: {GREEN}{', '.join(deallocated_jobs)}{RESET}")
    else:
        print(f"REMARKS: {YELLOW}No jobs cleared this set.{RESET}")
    print("="*85)

def display_final_allocation_table(os_sz, final_history):
    num_sets = len(final_history)
    print("\n" + BOLD + "JOB ALLOCATION FINAL SUMMARY (DYNAMIC PARTITION)".center(100) + RESET)
    
    # Header
    header = f"{'Partition Block':<15}"
    for i in range(1, num_sets + 1):
        header += f" | {f'Set {i}':<15}"
    
    line_length = len(header) + (num_sets * 2)
    print("=" * line_length)
    print(header)
    print("-" * line_length)

    # OS Row
    os_row = f"{'OS Area':<15}"
    for _ in range(num_sets):
        os_row += f" | {f'OS ({os_sz}K)':<15}"
    print(os_row)

    # Determine max partitions ever created in any set
    max_parts = max(len([b for b in set_mem if b['status'] != 'OS']) for set_mem in final_history)

    # Partitions Rows
    for p_idx in range(max_parts):
        p_name = f"P{p_idx + 1}"
        row = f"{p_name:<15}"
        
        for s_idx in range(num_sets):
            mem_state = [b for b in final_history[s_idx] if b['status'] != 'OS']
            
            if p_idx < len(mem_state):
                block = mem_state[p_idx]
                b_size = block['end'] - block['start']
                info = f"{block['status']} ({b_size}K)"
                row += f" | {info:<15}"
            else:
                row += f" | {'-':<15}"
        print(row)
    print("=" * line_length)

def main():
    clear_screen()
    print(CYAN + "="*85 + RESET)
    print(f"{BOLD}RELOCATABLE DYNAMIC PARTITION SCHEME (FCFS){RESET}".center(105))
    print(f"{BOLD}NAME: Ryan Paul J. Palacios{RESET}".center(105))
    print(CYAN + "="*85 + RESET)

    # 1. User Inputs
    try:
        memory_size = int(input("Enter Memory size (K unit): "))
        os_size = int(input("Enter OS size (K unit): "))

        if os_size >= memory_size:
            print(RED + "Error: OS size must be smaller than Memory size." + RESET)
            sys.exit()

        num_jobs = int(input("Enter No. of Jobs: "))
        jobs = []
        for i in range(num_jobs):
            j_size = int(input(f"Size of Job {i+1} (K): "))
            j_tat = int(input(f"TAT of Job {i+1}: "))
            jobs.append(Job(f"J{i+1}", j_size, j_tat))

    except ValueError:
        print(RED + "\nERROR: Please enter numbers only." + RESET)
        sys.exit()

    # Display initial Job List
    print("\n" + BOLD + "JOB LIST" + RESET)
    print(f"{'JOB':<10} | {'SIZE':<10} | {'TAT':<10}")
    print("-" * 35)
    for j in jobs:
        print(f"{j.name:<10} | {f'{j.size}K':<10} | {j.tat:<10}")

    memory = [
        {'start': 0, 'end': os_size, 'status': "OS"},
        {'start': os_size, 'end': memory_size, 'status': "Free"}
    ]

    waiting_queue = jobs.copy()
    running_jobs = []
    final_history = []
    turnaround = 1

    input("\nPress Enter to start simulation...")

    # 2. Simulation Loop (Sets)
    while waiting_queue or running_jobs:
        deallocated_this_set = []

        # --- DEALLOCATION PHASE ---
        finished_jobs = [j for j in running_jobs if j.remaining <= 0]
        for job in finished_jobs:
            deallocated_this_set.append(job.name)
            running_jobs.remove(job)

        # --- AUTOMATIC COMPACTION (RELOCATABLE) ---
        # Rebuild the memory map to automatically shift all running jobs contiguously
        memory = [{'start': 0, 'end': os_size, 'status': "OS"}]
        current_start = os_size
        
        for job in running_jobs:
            memory.append({
                'start': current_start,
                'end': current_start + job.size,
                'status': job.name
            })
            current_start += job.size
            
        # Add the single consolidated Free block at the end
        if current_start < memory_size:
            memory.append({
                'start': current_start,
                'end': memory_size,
                'status': "Free"
            })

        # --- ALLOCATION PHASE (Queue Skipping) ---
        jobs_to_remove = []
        for job in waiting_queue:
            # Laging sa pinakadulo ang Free block (if it exists)
            free_block = memory[-1]
            if free_block['status'] == "Free":
                free_size = free_block['end'] - free_block['start']
                
                if free_size >= job.size:
                    # Allocate the job
                    new_block = {
                        'start': free_block['start'],
                        'end': free_block['start'] + job.size,
                        'status': job.name
                    }
                    # Insert right before the Free block
                    memory.insert(-1, new_block)
                    free_block['start'] += job.size
                    
                    if free_block['start'] == free_block['end']:
                        memory.pop() # Remove Free block if exactly 0 space left
                        
                    job.allocated = True
                    running_jobs.append(job)
                    jobs_to_remove.append(job)
        
        # Remove allocated jobs from the waiting queue
        for job in jobs_to_remove:
            waiting_queue.remove(job)

        # --- RECORD & DISPLAY SET ---
        import copy
        final_history.append(copy.deepcopy(memory))
        
        # Note: I-adjust ang display_combined_table function call kung kinakailangan
        display_combined_table(os_size, memory, turnaround, deallocated_this_set, True)
        
        if not running_jobs and waiting_queue:
             job = waiting_queue[0]
             max_possible = memory_size - os_size
             if job.size > max_possible:
                 print(RED + f"\n[!] DEADLOCK: {job.name} ({job.size}K) is larger than max memory ({max_possible}K). Exiting." + RESET)
                 break

        input(f"Set {turnaround} complete. Press Enter to proceed...")

        # --- TIME UPDATE FOR NEXT SET ---
        for job in running_jobs:
            job.remaining -= 1
            
        turnaround += 1

    # --- FINAL SUMMARY ---
    print(CYAN + "\nFINAL CONSOLIDATED JOB ALLOCATION TABLE" + RESET)
    display_final_allocation_table(os_size, final_history)

    print("\n" + "="*85)
    print(BOLD + "CONCLUSION" + RESET)
    print("="*85)
    print("1. Relocatable Dynamic Partitioning automatically shifts active jobs contiguously.")
    print("2. Deallocated memory is instantly reclaimed and compacted to form one large free block.")
    print("3. Queue Skipping allows smaller jobs to execute if the largest contiguous block cannot accommodate the next job.")
    print("="*85)

if __name__ == "__main__":
    main()
