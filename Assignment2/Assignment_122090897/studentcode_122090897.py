state = {
    'bandwidth_history': [],
    'preferred_startup_rate': None,
}

def student_entrypoint(Measured_Bandwidth, Previous_Throughput, Buffer_Occupancy, Available_Bitrates, Video_Time, Chunk,
                       Rebuffering_Time, Preferred_Bitrate):

    chunk_num = int(Chunk['current'])
    buffer_size = Buffer_Occupancy['size']
    available_bitrates = sorted([int(k) for k in Available_Bitrates.keys()])
    Rk_list = available_bitrates
    m = len(Rk_list)

    # Save the Preferred_Bitrate, which could be None or actual bitrate in JSON file.
    if state['preferred_startup_rate'] is None:
        if Preferred_Bitrate:
            try:
                R_pre = int(Preferred_Bitrate)
            except ValueError:
                R_pre = Rk_list[0]
        else:
            R_pre = Rk_list[0]    # Default to lowest bitrate if Preferred_Bitrate is None in some cases
        state['preferred_startup_rate'] = R_pre
    else:
        R_pre = state['preferred_startup_rate']

    # Update bandwidth history
    if Previous_Throughput > 0:
        bandwidth_measurement = Previous_Throughput  # Use the real throughput from the last chunk
    else:
        bandwidth_measurement = Measured_Bandwidth

    state['bandwidth_history'].append(bandwidth_measurement)

    # Rate based switching:
    # Depth：Use last 3 or fewer
    depth = min(6, len(state['bandwidth_history']))
    # The last 5 or less previous bandwidths are used for bandwidth estimation
    recent_bandwidths = state['bandwidth_history'][-depth:]
    if chunk_num > 0:
        N_buf = buffer_size  # The buffer size in chunk numbers
    else:
        N_buf = 1  # Default to 1 if chunk_time is zero to avoid divided by zero

    sum_bw = 0
    for j in range(depth):
        sum_bw += recent_bandwidths[-(j+1)] * max((1 - (j / N_buf)), 0)
    Bandwidth = sum_bw / depth  # Estimated bandwidth

    # Bitrate decision
    R_min = float('inf')
    R_max = 0
    for Rk in Rk_list:
        if R_max < Rk and Rk < Bandwidth:
            R_max = Rk
            print("Rk：")
            print(Rk)
            print("Bandwidth：")
            print(Bandwidth)
        if R_min > Rk:
            R_min = Rk

    if R_max > 0:
        Rs = R_max
    else:
        Rs = R_min

    # Preferred startup switching：the player is in the startup phase and the suggested rate is smaller
    # than the preferred rate
    if Video_Time < 10:
        s = Rs  # The rate suggested by Rate based switching
        for Rk in reversed(Rk_list):
            if Rk == s:
                return Rs
            if Rk <= R_pre:
                return Rk
        return Rk_list[m-1]
    else:
        return Rs
