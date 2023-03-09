#!/bin/bash


API_URL="https://netbox.aptportfolio.com/api/dcim/devices/?rack_id=24"
API_TOKEN="884b634fc254fc94dce941b84d2a7181dad9afaf"
HPE="HPE"
Supermicro="Supermicro"
MODELS="nemo|beast|bhim|kim|ld4|ninja"

get_device_list() {
    curl -s -X GET "$API_URL" \
        -H "accept: application/json" \
        -H "Authorization: Token $API_TOKEN" | jq -r '.results[] | .display_name'
}

get_power_supply_info() {
    local device_name=$1
    local device_manufacturer=$(ssh ansible_usr@"$device_name" sudo dmidecode -s system-manufacturer)

    if [[ "$device_manufacturer" == "HPE" ]]; then
        ssh ansible_usr@"$device_name" "sudo ipmitool sdr type 'Power Supply' | grep 'Output' | cut -d'|' -f5 | awk '{s+=\$1} END {print s,\$2}'"
    elif [[ "$device_manufacturer" == "Supermicro" ]]; then
        ssh ansible_usr@"$device_name" "sudo ipmitool dcmi power reading | grep Instant | awk '{print \$4 \" \" \$5}'"
    else
        ssh ansible_usr@"$device_name" " sudo ipmitool sdr type 'Power Supply' | grep POUT | cut -d'|' -f5 | awk '{s+=\$1} END {print s,\$2}'"
    fi
}

main() {
    total_power_consumption=0
    device_list=$(get_device_list | grep -E "$MODELS" | grep -v "[0-9]{8}")

    for device_name in $device_list; do
        power_consumption=$(get_power_supply_info "$device_name" | awk '{print $1}')

        if [[ -n "$power_consumption" ]]; then
            total_power_consumption=$(echo "$total_power_consumption + $power_consumption" | bc)
            printf "%s: %d W\n" "$device_name" "$power_consumption"
        else
            echo "$device_name: Unable to retrieve power consumption"
        fi
    done

    echo "Total power consumption: $total_power_consumption W"
}

main
