import serial
import struct
import statistics
import socket

#tty = "/dev/imu"
tty = "/dev/ttyACM0"
 
ser = serial.Serial(tty, 115200, timeout=2, xonxoff=False, rtscts=False, dsrdtr=False)
 
ser.flushInput()
ser.flushOutput()
print("Hello NGIMU, let's get the data!")
 
valid_x = 0
valid_y = 0
valid_z = 0
 
med_x = 0
med_y = 0
med_z = 0
 
#initialize control for reading OSC /euler messages
euler=bytearray()
arr_x=[]
arr_y=[]
arr_z=[]
t_out = 0
final_z = 0
euler_ctr = 100
stat_counter = 0


UDP_IP = "127.0.0.1"
UDP_PORT=5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   

 
#infinite loop that reads serial interface char by char
while True:
    bytesToRead = ser.inWaiting()
    message = ser.read(1)
    euler_ctr += 1
 
#before every /euler an 0x1c byte occurs (don't know why), thus we use it to determine that /euler OSC message is coming next
#when finding this byte, we clear the corresponding variables
    if message[0] == 28:
        euler.clear()
        euler_ctr = 0
 
 
#reading the whole /euler OSC message char by char (from Ox1c to # of next OSC #bundle)
    if euler_ctr < 31:
        #print(message[0])
        euler.append(message[0])
 
    if euler_ctr == 2 and euler[2] != 101:
        euler_ctr = 50
        euler.clear()
 
#deleting starting and terminating byte (0x1c and #)
    if euler_ctr == 31:
        del euler[0]
        del euler[-1]
 
 
#each argument is a 32bit float, thus consisting of 4 bytes
#slicing arrays to get separate 4-byte arrays of each value
        x_axis = euler[16:20]
        y_axis = euler[20:24]
        z_axis = euler[24:28]
        #print(x_axis, y_axis, z_axis)
 
#turning 4 bytes of an array to a big endian 32 bit floating point value
        f_y_axis = struct.unpack('>f', y_axis)
        f_x_axis = struct.unpack('>f', x_axis)
        f_z_axis = struct.unpack('>f', z_axis)
 
        if (f_y_axis[0] < 180 and f_y_axis[0] > 0.05) or (f_y_axis[0] > -180 and f_y_axis[0] < -0.05):
            valid_y = f_y_axis[0]
        if f_x_axis[0] < 180 and f_x_axis[0] > -180 and f_x_axis[0] != 0:
            valid_x = f_x_axis[0]
        if (f_z_axis[0] < 180 and f_z_axis[0] > 0.05) or (f_z_axis[0] > -180 and f_z_axis[0] < -0.05):
            valid_z = f_z_axis[0]
 
        if stat_counter < 2:
            stat_counter += 1
            arr_x.append(valid_x)
            arr_y.append(valid_y)
            arr_z.append(valid_z)
 
        if stat_counter == 2:
            stat_counter = 0
            med_x = statistics.mean(arr_x)
            med_y = statistics.median(arr_y)
            med_z = statistics.mean(arr_z)


                #print("Failover: ", med_z)
                #print("fin", final_z)
            #print(med_x)
            arr_x.clear()
            arr_y.clear()
            arr_z.clear()
 
 
 
#printing value
        #print("Euler: ", euler)
        #print("Kompas: ", valid_z, " Naklonenie X: ", valid_x, " Naklonenie Y: ", valid_y)
            print("Compass:", med_z, "X skew:", med_x, "Y skew:", med_y)
            #print(euler)
            #print(f_z_axis)
            bytes_x = bytearray(struct.pack(">f",med_x))
            bytes_y = bytearray(struct.pack(">f",med_y))
            bytes_z = bytearray(struct.pack(">f",med_z))
            message= bytes_x + bytes_y + bytes_z
            sock.sendto(message, (UDP_IP, UDP_PORT))
            #print("Sent: ", med_z)


