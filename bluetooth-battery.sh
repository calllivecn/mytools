
echo "键盘电量："
bluetoothctl info "EC:BE:10:91:2E:04" |grep "Battery Percentage"


echo "鼠标电量："
bluetoothctl info "D1:02:38:20:11:DD" |grep "Battery Percentage"

