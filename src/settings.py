MAX_BATCH_SIZE = 200000 #could be any int, max tested value was 10**6, optimal value depends on quality of system parts
WORKTIME = 120 #if 0 program will work endlessly; must be non_negative

online_check_time = 3 #time between online_status ckecks for availiable hosts
ask_data_time = 10 #batch handler will go to sleep if batch is empty
wait_for_new_files = 300 #time between coordinator looks for new files to read

BIO = "user"