# NanoVNA README capture

Generated: 2026-06-07T00:36:49  
Library model preset: `NANOVNA_F_V2`  
Captured verbatim via `command()` passthrough (raw device bytes, no library filtering). Paste the Example Return blocks into the README's per-command reference as desired.

---

## `info`  (device SW/HW info)

* **sent:** `info`
* **raw return:**

  ```
  b'Model:        NanoVNA-F_V2\r\nFrequency:    50k ~ 3GHz\r\nBuild time:   Aug 17 2021 - 16:13:15 CST\r\nch> \r\nch> '
  ```

## `version`  (firmware version string)

* **sent:** `version`
* **raw return:**

  ```
  b'0.3.0\r\nch> \r\nch> '
  ```

## `SN`  (unique serial number)

* **sent:** `SN`
* **raw return:**

  ```
  b'20210413080156D7\r\nch> \r\nch> '
  ```

## `resolution`  (LCD resolution)

* **sent:** `resolution`
* **raw return:**

  ```
  b'800,480\r\nch> \r\nch> '
  ```

## `LCD_ID`  (LCD controller id)

* **sent:** `LCD_ID`
* **raw return:**

  ```
  b'118200\r\nch> \r\nch> '
  ```

## `help`  (full command list + usage)

* **sent:** `help`
* **raw return:**

  ```
  b'There are all commands\r\nhelp:                lists all the registered commands\r\nreset:               usage: reset\r\ncwfreq:              usage: cwfreq {frequency(Hz)}\r\nsaveconfig:          usage: savec ... 'rsion\r\ninfo:                usage: NanoVNA-F V2 info\r\nSN:                  usage: NanoVNA-F V2 Serial Numbel\r\nresolution:          usage: LCD resolution\r\nLCD_ID:              usage: LCD ID\r\nch> \r\nch> '  (total 1414 bytes)
  ```

## `cal`  (calibration status (no arg))

* **sent:** `cal`
* **raw return:**

  ```
  b"load open short thru cal'ed \r\nch> \r\nch> "
  ```

## `edelay`  (current electrical delay)

* **sent:** `edelay`
* **raw return:**

  ```
  b'0.000000\r\nch> \r\nch> '
  ```

## `cwfreq`  (cwfreq with no arg)

* **sent:** `cwfreq`
* **raw return:**

  ```
  b'usage: cwfreq {frequency(KHz)}\r\nch> \r\nch> '
  ```

## `sweep`  (current sweep settings (no arg))

* **sent:** `sweep`
* **raw return:**

  ```
  b'50000 3000000000 101\r\nch> \r\nch> '
  ```

## `marker`  (active marker info (no arg))

* **sent:** `marker`
* **raw return:**

  ```
  b'1 0 50000\r\nch> \r\nch> '
  ```

## `trace`  (active trace attributes (no arg))

* **sent:** `trace`
* **raw return:**

  ```
  b'0\tLOGMAG\tS11\t10.000000\t7.000000\r\n1\tLOGMAG\tS21\t10.000000\t7.000000\r\n2\tSMITH\tS11\t1.000000\t0.000000\r\nch> \r\nch> '
  ```

## `data 0`  (S11)

* **sent:** `data 0`
* **raw return:**

  ```
  b'1.007216 -0.004928\r\n0.990002 -0.086659\r\n0.979805 -0.166614\r\n0.955808 -0.259103\r\n0.933080 -0.323376\r\n0.895773 -0.404512\r\n0.822972 -0.492628\r\n0.819286 -0.529689\r\n0.741957 -0.619298\r\n0.650872 -0.675496\r\n ... '\n-0.559925 -0.284956\r\n-0.551666 -0.284232\r\n-0.564699 -0.276427\r\n-0.563888 -0.259965\r\n-0.573843 -0.255513\r\n-0.564694 -0.243419\r\n-0.570665 -0.243051\r\n-0.575692 -0.266697\r\n-0.594587 -0.252904\r\nch> \r\nch> '  (total 2094 bytes)
  ```

## `data 1`  (S21)

* **sent:** `data 1`
* **raw return:**

  ```
  b'-0.000001 -0.000020\r\n-0.000054 -0.000048\r\n0.000038 0.000033\r\n0.000018 0.000007\r\n0.000020 -0.000018\r\n0.000028 0.000031\r\n-0.000034 0.000040\r\n0.000013 0.000029\r\n-0.000015 -0.000044\r\n-0.000018 -0.000029\r\n ... ' 0.000458\r\n0.000118 0.000306\r\n-0.000016 0.000123\r\n-0.000159 0.000114\r\n-0.000026 0.000385\r\n0.000174 0.000221\r\n-0.000226 0.000008\r\n-0.000417 -0.000018\r\n-0.000271 0.000175\r\n-0.000214 0.000073\r\nch> \r\nch> '  (total 2038 bytes)
  ```

## `data 2`  (cal load)

* **sent:** `data 2`
* **raw return:**

  ```
  b'-0.112505 0.955492\r\n1.048636 -0.092794\r\n1.023569 -0.140577\r\n1.004384 -0.186833\r\n0.986771 -0.235588\r\n0.967552 -0.285482\r\n0.946620 -0.331954\r\n0.924722 -0.376209\r\n0.901601 -0.419227\r\n0.876987 -0.461830\r\n ... '1.644274\r\n-0.469211 1.684736\r\n-0.398832 1.761435\r\n-0.339071 1.792552\r\n-0.331459 1.807672\r\n-0.283420 1.834478\r\n-0.211461 1.880333\r\n-0.136420 1.853601\r\n-0.059036 1.835470\r\n-0.007701 1.772903\r\nch> \r\nch> '  (total 2060 bytes)
  ```

## `data 3`  (cal open)

* **sent:** `data 3`
* **raw return:**

  ```
  b'0.204650 -0.874273\r\n-0.910306 0.055119\r\n-0.898200 0.070266\r\n-0.903037 0.091403\r\n-0.909429 0.121395\r\n-0.899323 0.154398\r\n-0.904639 0.191514\r\n-0.908359 0.231502\r\n-0.907371 0.275764\r\n-0.903601 0.321900\r\n ... '\n-0.148623 -1.676195\r\n-0.236308 -1.756096\r\n-0.289429 -1.803876\r\n-0.359331 -1.854254\r\n-0.416402 -1.846695\r\n-0.491473 -1.881484\r\n-0.543695 -1.855998\r\n-0.608137 -1.808079\r\n-0.603274 -1.731765\r\nch> \r\nch> '  (total 2017 bytes)
  ```

## `data 4`  (cal short)

* **sent:** `data 4`
* **raw return:**

  ```
  b'0.019303 0.015509\r\n0.009293 -0.001851\r\n0.009898 -0.004896\r\n0.010149 -0.006496\r\n0.009532 -0.008068\r\n0.009706 -0.010298\r\n0.009131 -0.011977\r\n0.009278 -0.014292\r\n0.008603 -0.016631\r\n0.008475 -0.018607\r\n0 ... '07493\r\n-0.236910 -0.001862\r\n-0.243219 0.006463\r\n-0.255856 -0.006541\r\n-0.260763 -0.000943\r\n-0.279433 0.016014\r\n-0.286452 0.019108\r\n-0.289231 0.018658\r\n-0.276452 0.042624\r\n-0.258535 0.050172\r\nch> \r\nch> '  (total 2104 bytes)
  ```

## `data 5`  (cal thru)

* **sent:** `data 5`
* **raw return:**

  ```
  b'0.682167 0.132813\r\n1.694839 -0.244819\r\n1.617428 -0.272450\r\n1.588461 -0.320023\r\n1.573227 -0.380498\r\n1.514157 -0.439401\r\n1.521592 -0.516664\r\n1.520946 -0.604656\r\n1.522906 -0.705325\r\n1.511809 -0.818436\r\n1 ... '2.897280\r\n2.779549 -2.921140\r\n2.533177 -3.010962\r\n2.367419 -3.083631\r\n2.310764 -3.082323\r\n2.240031 -3.126175\r\n2.168901 -3.290086\r\n2.069663 -3.368516\r\n1.925121 -3.511241\r\n1.707820 -3.634449\r\nch> \r\nch> '  (total 2033 bytes)
  ```

## `data 6`  (cal isolation)

* **sent:** `data 6`
* **raw return:**

  ```
  b'0.000012 0.000013\r\n0.000016 0.000071\r\n-0.000058 -0.000071\r\n-0.000000 -0.000002\r\n0.000006 0.000063\r\n-0.000056 -0.000004\r\n-0.000008 -0.000022\r\n-0.000013 -0.000006\r\n0.000053 0.000040\r\n-0.000027 0.000034\r ... '0779\r\n0.001216 -0.000187\r\n0.001530 -0.000703\r\n0.001902 -0.001579\r\n0.002120 -0.004519\r\n0.000617 -0.005699\r\n-0.001305 -0.006307\r\n-0.002245 -0.006565\r\n-0.003409 -0.005532\r\n-0.003362 -0.004249\r\nch> \r\nch> '  (total 2027 bytes)
  ```

## `scan 1000000 2000000 11 1`  (scan outmask 1 -> frequencies)

* **sent:** `scan 1000000 2000000 11 1`
* **raw return:**

  ```
  b'1000000 \r\n1100000 \r\n1200000 \r\n1300000 \r\n1400000 \r\n1500000 \r\n1600000 \r\n1700000 \r\n1800000 \r\n1900000 \r\n2000000 \r\nch> \r\nch> '
  ```

## `scan 1000000 2000000 11 2`  (scan outmask 2 -> S11 pairs)

* **sent:** `scan 1000000 2000000 11 2`
* **raw return:**

  ```
  b'1.097607 1.186987 \r\n1.155769 1.300400 \r\n1.228313 1.402045 \r\n1.320642 1.491982 \r\n1.431919 1.565192 \r\n1.558024 1.602562 \r\n1.692939 1.612919 \r\n1.827417 1.584750 \r\n1.944079 1.523165 \r\n2.040512 1.427915 \r\n2.108881 1.318900 \r\nch> \r\nch> '
  ```

## `scan 1000000 2000000 11 6`  (scan outmask 6 -> S11+S21)

* **sent:** `scan 1000000 2000000 11 6`
* **raw return:**

  ```
  b'1.098073 1.185413 0.000053 0.000123 \r\n1.152543 1.296921 -0.000052 -0.000138 \r\n1.229702 1.403980 -0.000084 -0.000011 \r\n1.323767 1.490617 -0.000049 -0.000166 \r\n1.434114 1.562207 0.000143 0.000166 \r\n1.56 ... '522 1.612386 -0.000054 -0.000028 \r\n1.826490 1.588547 0.000025 0.000240 \r\n1.944057 1.523736 0.000113 0.000038 \r\n2.042630 1.430430 -0.000354 -0.000046 \r\n2.107389 1.319881 0.000248 -0.000137 \r\nch> \r\nch> '  (total 439 bytes)
  ```

## `scan 1000000 2000000 11 7`  (scan outmask 7 -> freq+S11+S21)

* **sent:** `scan 1000000 2000000 11 7`
* **raw return:**

  ```
  b'1000000 1.098258 1.188245 -0.000036 0.000027 \r\n1100000 1.153075 1.299057 -0.000010 0.000002 \r\n1200000 1.228164 1.404621 -0.000087 -0.000060 \r\n1300000 1.319376 1.490853 0.000185 -0.000092 \r\n1400000 1.4 ... '1700000 1.826611 1.582846 -0.000017 -0.000028 \r\n1800000 1.942879 1.525207 -0.000122 -0.000148 \r\n1900000 2.034380 1.430548 0.000159 0.000036 \r\n2000000 2.108886 1.317611 -0.000143 -0.000226 \r\nch> \r\nch> '  (total 531 bytes)
  ```

## `frequencies`  (freqs from last sweep)

* **sent:** `frequencies`
* **raw return:**

  ```
  b'1000000\r\n1100000\r\n1200000\r\n1300000\r\n1400000\r\n1500000\r\n1600000\r\n1700000\r\n1800000\r\n1900000\r\n2000000\r\nch> \r\nch> '
  ```

## `scan 1000000 2000000 999 2`  (over-max points (error string))

* **sent:** `scan 1000000 2000000 999 2`
* **raw return:**

  ```
  b'sweep points exceeds range 11 -201\r\nch> \r\nch> '
  ```

---

## Authoritative `help` usage strings (for 'Original Usage' fields)

```
There are all commands
help:                lists all the registered commands
reset:               usage: reset
cwfreq:              usage: cwfreq {frequency(Hz)}
saveconfig:          usage: saveconfig
clearconfig:         usage: clearconfig {protection key}
data:                usage: data [array]
frequencies:         usage: frequencies
scan:                usage: scan {start(Hz)} {stop(Hz)} [points] [outmask]
sweep:               usage: sweep [start(Hz)] [stop(Hz)] [points]
touchcal:            usage: touchcal
touchtest:           usage: touchtest
pause:               usage: pause
resume:              usage: resume
cal:                 usage: cal [load|open|short|thru|done|reset|on|off]
save:                usage: save {id}
recall:              usage: recall {id}
trace:               usage: trace [0|1|2|3|all] [{format}|scale|refpos|channel|off] [{value}]
marker:              usage: marker [1|2|3|4] [on|off|{index}]
edelay:              usage: edelay {value}
pwm:                 usage: pwm {0.0-1.0}
beep:                usage: beep on/off
lcd:                 usage: lcd X Y WIDTH HEIGHT FFFF
capture:             usage: capture
version:             usage: Show NanoVNA version
info:                usage: NanoVNA-F V2 info
SN:                  usage: NanoVNA-F V2 Serial Numbel
resolution:          usage: LCD resolution
LCD_ID:              usage: LCD ID
ch> 
ch> 
```
