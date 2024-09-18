import time

def handle_variable_length(value, base_length=28):
    if value == None:
        return base_length,base_length
    n_bars = base_length - len(value)
    n_bars_even = n_bars % 2 == 0
    n_bars_side_l = n_bars // 2
    n_bars_side_r = n_bars_side_l
    if not n_bars_even: n_bars_side_r += 1
    return n_bars_side_l, n_bars_side_r


def print_data(response, probe_name, expected_ph= None, base_width=28):
    now = time.asctime() 
    ph = f"{response.ph_high_res:.2f}" if response.ph_high_res != None else 'None'
    temp = f"{response.temperature:.1f}" if response.temperature != None else 'None'
    width = max(len(probe_name), len('ph: ')+len(ph), len('temp[°C]: ')+len(temp), len(now), base_width)

    # handle variable length of probe_name, edge cases might be possible
    n_bars_heading_side_l, n_bars_heading_side_r = handle_variable_length(probe_name, width)
    n_bars_ph_side_l, n_bars_ph_side_r = handle_variable_length(ph, width-len('ph: '))
    n_bars_temp_side_l, n_bars_temp_side_r = handle_variable_length(temp, width-len('temp[°C]: '))
    n_bars_time_side_l, n_bars_time_side_r = handle_variable_length(now, width)
    if expected_ph != None:
        n_bars_expected_ph_side_l, n_bars_expected_ph_side_r = handle_variable_length(f"expected ph: {expected_ph:.2f}", width)

    print(f'┌{"─"*n_bars_heading_side_l}{probe_name}{"─"*n_bars_heading_side_r}┐')
    print(f'├{"─"*n_bars_time_side_l}{now}{"─"*n_bars_time_side_r}┤')
    print(f'│{" "*n_bars_ph_side_l}ph: {ph}{" "*n_bars_ph_side_r}│')
    if expected_ph != None:
        print(f'│{" "*n_bars_expected_ph_side_l}expected ph: {expected_ph:.2f}{" "*n_bars_expected_ph_side_r}│')
    print(f'│{" "*n_bars_temp_side_l}temp[°C]: {temp}{" "*n_bars_temp_side_r}│')
    print(f'└{"─"*width}┘')

def print_data_oneline(response, probe_name):
    print(f'{time.asctime()} {probe_name} ph: {response.ph_high_res} temp[°C]: {response.temperature}')

#---------------------------------------------------------
# Example

if __name__ == '__main__':
    #example print
    response1 = type('Response', (object,),{
        'ph_high_res': 7.00,
        'ph_low_res': 7.0,
        'temperature': 25.0
    })()
    response2 = type('Response', (object,),{
            'ph_high_res': None,
            'ph_low_res': None,
            'temperature': 24.5
        })()
    print_data(response1, 'probe1')
    print_data(response2, 'probe2')
    print_data(response2, 'probe20')
    print_data(response2, '20')
    print_data(response2, '', base_width=1)
    print_data(response2, 'very long name increase width to make it fit', base_width=45)
    print_data(response2, 'very long name increase width to make it fit') # test auto width