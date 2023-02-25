# Class used to discretize data which is continuously collected from the zsc
# load cells. Peaks of the loading waveforms are found then saved.
import random
import gc

class PeakExtr:
    """
    Takes in a vector v from the columns of load_prof_df,
    delta is the threshold value for classifying a value as a possible maximum/peak.
    """
    def __init__(self, pw):
        self.patient_weight = pw
        self.first_time_stamp = ''
        self.time_stamp_iterator = 0


    def peak_det_elect(self, in_v, delta, pw):
        # Variable for keeping track of the min and max indices

        mn = 10000
        mx = -10000
        min_pos = 0
        max_time_stamp = ''
        look_for_max = True
        found_peaks = []

        self.time_stamp_iterator = 0

        for i in range(0, len(in_v) - 1):

            self.time_stamp_iterator += 1
            # [0.0, -50, 0.0, '2022-08-17T13:58:43']
            # Checking for min or max values, and collecting their index

            curr_time_stamp = in_v[i]

            # Ensure Nones do not mess up the script
            if curr_time_stamp == None:
                continue

            #print("Current Time Stamp:\t", curr_time_stamp)
            #print("Current i ", i)

            # If one of the sensors is messed up then skip over its data
            if float(curr_time_stamp[0]) <= -45.0 or float(curr_time_stamp[1]) <= -45.0 or float(curr_time_stamp[2]) <= -45.0:
                continue
            if float(curr_time_stamp[0]) <= -20.0 or float(curr_time_stamp[1]) <= -20.0 or float(curr_time_stamp[2]) <= -20.0:
                continue

            check_index = (float(curr_time_stamp[0]) + float(curr_time_stamp[1]) + float(curr_time_stamp[2]))

            check_index = check_index / 3

            check_index = (check_index / pw)
            check_index = check_index * 100

            # 16 samples is 1 second, so no other maxes are collected
            if check_index > mx: #and num_samples_from_last_max > 16
                mx = check_index
                max_time_stamp = self.first_time_stamp

            if check_index < mn:
                mn = check_index
                min_pos = self.first_time_stamp

            if look_for_max == True:
                # Also do a spacing check for 0.75 seconds in between samples
                # May need to go up
                if check_index < mx - delta:
                    found_peaks.append([max_time_stamp, mx])

                    mn = check_index
                    min_pos = self.first_time_stamp
                    look_for_max = False
            else:
                if check_index > mn + delta:
                    #min_arr = np.append(min_arr, np.array([[min_pos, mn]]), axis=0)
                    mx = check_index
                    print(self.first_time_stamp)
                    max_time_stamp = self.first_time_stamp
                    look_for_max = True

        # result[0] will return max_arr and result[1] will return min_arr
        # In each array, column 0 will have the index, column 1 will have the value
        return found_peaks

    def peak_extr(self, in_v, first_time_stamp):

        self.first_time_stamp = first_time_stamp
        # First run of peak_det to find approximate peaks then adjust the delta value
        # for peak thresholds
        first_pass_arr = self.peak_det_elect(in_v, 5, self.patient_weight)

        if len(first_pass_arr) > 3:
            # Generating a randomly permuted vector
            #perm_vect = np.random.randint(0, high=max_arr.shape[0], size=10, dtype=int)
            perm_vect = [random.randint(0, len(first_pass_arr) - 1) for x in range(0, 10)]
            check_random_peak = []
            for n in range(0, 10):
                # Random row, column 1 has max value
                check_random_peak.append(first_pass_arr[perm_vect[n]])

            mean_load = 0
            for x in range(0, len(check_random_peak)):
                curr_val = check_random_peak[x]
                mean_load += curr_val[1]

            mean_load = mean_load / len(check_random_peak)
        else:
            mean_load = 5

        # Setting the distance between time samples
        num_samp = 0
        # Delta value for load established at 40% of the samples load
        # Changing to 5 to experiment and see if lower weight bearing values can be captured.
        Delta = 0.4 * mean_load
        if Delta <= 5:
            Delta = 5

        # New peak detection tables using delta insqtead of patient weight
        second_pass = self.peak_det_elect(in_v, Delta, self.patient_weight)

        with open("/sd/peak_det_save.txt", "a") as peak_det_file:
            # for x in range(0, Q.size):
            for x in range(0, len(second_pass)):
                curr_val = second_pass[x]
                stringed_arr = '\t'.join(map(str, [curr_val[0], curr_val[1]]))
                # print(stringed_arr)
                peak_det_file.write(stringed_arr + "\n")
                if (x == len(second_pass) - 2):
                    peak_det_file.write("-----------------" + "\n")

        # Ensuring no memory is being wasted after here
        gc.collect()
