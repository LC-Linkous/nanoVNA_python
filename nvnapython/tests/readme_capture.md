# NanoVNA README capture

Generated: 2026-06-12T22:19:21  
Library model preset: `NANOVNA_F_V2`  
Captured verbatim via `command()` passthrough (raw device bytes, no library filtering). Paste the Example Return blocks into the README's per-command reference as desired.

---

## `info`  (device SW/HW info)

* **sent:** `info`
* **raw return:**

  ```
  b'Model:        NanoVNA-F_V2\r\nFrequency:    50k ~ 3GHz\r\nBuild time:   Aug 17 2021 - 16:13:15 CST'
  ```

## `version`  (firmware version string)

* **sent:** `version`
* **raw return:**

  ```
  b'0.3.0'
  ```

## `SN`  (unique serial number)

* **sent:** `SN`
* **raw return:**

  ```
  b'20210413080156D7'
  ```

## `resolution`  (LCD resolution)

* **sent:** `resolution`
* **raw return:**

  ```
  b'800,480'
  ```

## `LCD_ID`  (LCD controller id)

* **sent:** `LCD_ID`
* **raw return:**

  ```
  b'118200'
  ```

## `help`  (full command list + usage)

* **sent:** `help`
* **raw return:**

  ```
  b'There are all commands\r\nhelp:                lists all the registered commands\r\nreset:               usage: reset\r\ncwfreq:              usage: cwfreq {frequency(Hz)}\r\nsaveconfig:          usage: savec ... 'w NanoVNA version\r\ninfo:                usage: NanoVNA-F V2 info\r\nSN:                  usage: NanoVNA-F V2 Serial Numbel\r\nresolution:          usage: LCD resolution\r\nLCD_ID:              usage: LCD ID'  (total 1402 bytes)
  ```

## `cal`  (calibration status (no arg))

* **sent:** `cal`
* **raw return:**

  ```
  b"load open short thru cal'ed "
  ```

## `edelay`  (current electrical delay)

* **sent:** `edelay`
* **raw return:**

  ```
  b'0.000000'
  ```

## `cwfreq`  (cwfreq with no arg)

* **sent:** `cwfreq`
* **raw return:**

  ```
  b'usage: cwfreq {frequency(KHz)}'
  ```

## `sweep`  (current sweep settings (no arg))

* **sent:** `sweep`
* **raw return:**

  ```
  b'50000 3000000000 101'
  ```

## `marker`  (active marker info (no arg))

* **sent:** `marker`
* **raw return:**

  ```
  b'1 0 50000'
  ```

## `trace`  (active trace attributes (no arg))

* **sent:** `trace`
* **raw return:**

  ```
  b'0\tLOGMAG\tS11\t10.000000\t7.000000\r\n1\tLOGMAG\tS21\t10.000000\t7.000000\r\n2\tSMITH\tS11\t1.000000\t0.000000'
  ```

## `data 0`  (S11)

* **sent:** `data 0`
* **raw return:**

  ```
  b'1.003241 -0.003750\r\n0.991068 -0.103577\r\n0.974471 -0.206998\r\n0.944884 -0.309481\r\n0.902258 -0.402777\r\n0.850426 -0.491849\r\n0.788785 -0.574595\r\n0.718225 -0.649316\r\n0.641057 -0.714157\r\n0.557581 -0.770238\r\n ... '7188 -0.342591\r\n-0.293669 -0.305931\r\n-0.336853 -0.259301\r\n-0.380336 -0.209556\r\n-0.424363 -0.150488\r\n-0.460049 -0.095136\r\n-0.462895 -0.017809\r\n-0.479859 0.062354\r\n-0.477680 0.130272\r\n-0.459177 0.203043'  (total 2033 bytes)
  ```

## `data 1`  (S21)

* **sent:** `data 1`
* **raw return:**

  ```
  b'-0.000051 0.000009\r\n-0.000028 -0.000044\r\n0.000007 0.000071\r\n0.000017 -0.000002\r\n0.000015 -0.000053\r\n0.000014 0.000013\r\n0.000012 0.000017\r\n0.000025 -0.000033\r\n-0.000020 0.000008\r\n-0.000002 -0.000010\r\n0 ... '164\r\n0.000198 0.000569\r\n-0.000008 0.000479\r\n0.000042 0.000323\r\n-0.000190 0.000306\r\n-0.000281 0.000287\r\n-0.000458 0.000472\r\n-0.000359 0.000852\r\n-0.000253 0.000880\r\n-0.000001 0.000771\r\n0.000143 0.000591'  (total 2019 bytes)
  ```

## `data 2`  (cal load)

* **sent:** `data 2`
* **raw return:**

  ```
  b'-0.112505 0.955492\r\n1.048636 -0.092794\r\n1.023569 -0.140577\r\n1.004384 -0.186833\r\n0.986771 -0.235588\r\n0.967552 -0.285482\r\n0.946620 -0.331954\r\n0.924722 -0.376209\r\n0.901601 -0.419227\r\n0.876987 -0.461830\r\n ... '\r\n-0.501903 1.644274\r\n-0.469211 1.684736\r\n-0.398832 1.761435\r\n-0.339071 1.792552\r\n-0.331459 1.807672\r\n-0.283420 1.834478\r\n-0.211461 1.880333\r\n-0.136420 1.853601\r\n-0.059036 1.835470\r\n-0.007701 1.772903'  (total 2048 bytes)
  ```

## `data 3`  (cal open)

* **sent:** `data 3`
* **raw return:**

  ```
  b'0.204650 -0.874273\r\n-0.910306 0.055119\r\n-0.898200 0.070266\r\n-0.903037 0.091403\r\n-0.909429 0.121395\r\n-0.899323 0.154398\r\n-0.904639 0.191514\r\n-0.908359 0.231502\r\n-0.907371 0.275764\r\n-0.903601 0.321900\r\n ... '5 -1.613203\r\n-0.148623 -1.676195\r\n-0.236308 -1.756096\r\n-0.289429 -1.803876\r\n-0.359331 -1.854254\r\n-0.416402 -1.846695\r\n-0.491473 -1.881484\r\n-0.543695 -1.855998\r\n-0.608137 -1.808079\r\n-0.603274 -1.731765'  (total 2005 bytes)
  ```

## `data 4`  (cal short)

* **sent:** `data 4`
* **raw return:**

  ```
  b'0.019303 0.015509\r\n0.009293 -0.001851\r\n0.009898 -0.004896\r\n0.010149 -0.006496\r\n0.009532 -0.008068\r\n0.009706 -0.010298\r\n0.009131 -0.011977\r\n0.009278 -0.014292\r\n0.008603 -0.016631\r\n0.008475 -0.018607\r\n0 ... '0.223067 0.007493\r\n-0.236910 -0.001862\r\n-0.243219 0.006463\r\n-0.255856 -0.006541\r\n-0.260763 -0.000943\r\n-0.279433 0.016014\r\n-0.286452 0.019108\r\n-0.289231 0.018658\r\n-0.276452 0.042624\r\n-0.258535 0.050172'  (total 2092 bytes)
  ```

## `data 5`  (cal thru)

* **sent:** `data 5`
* **raw return:**

  ```
  b'0.682167 0.132813\r\n1.694839 -0.244819\r\n1.617428 -0.272450\r\n1.588461 -0.320023\r\n1.573227 -0.380498\r\n1.514157 -0.439401\r\n1.521592 -0.516664\r\n1.520946 -0.604656\r\n1.522906 -0.705325\r\n1.511809 -0.818436\r\n1 ... '\r\n2.986886 -2.897280\r\n2.779549 -2.921140\r\n2.533177 -3.010962\r\n2.367419 -3.083631\r\n2.310764 -3.082323\r\n2.240031 -3.126175\r\n2.168901 -3.290086\r\n2.069663 -3.368516\r\n1.925121 -3.511241\r\n1.707820 -3.634449'  (total 2021 bytes)
  ```

## `data 6`  (cal isolation)

* **sent:** `data 6`
* **raw return:**

  ```
  b'0.000012 0.000013\r\n0.000016 0.000071\r\n-0.000058 -0.000071\r\n-0.000000 -0.000002\r\n0.000006 0.000063\r\n-0.000056 -0.000004\r\n-0.000008 -0.000022\r\n-0.000013 -0.000006\r\n0.000053 0.000040\r\n-0.000027 0.000034\r ... '.001404 0.000779\r\n0.001216 -0.000187\r\n0.001530 -0.000703\r\n0.001902 -0.001579\r\n0.002120 -0.004519\r\n0.000617 -0.005699\r\n-0.001305 -0.006307\r\n-0.002245 -0.006565\r\n-0.003409 -0.005532\r\n-0.003362 -0.004249'  (total 2015 bytes)
  ```

## `scan 1000000 2000000 11 1`  (scan outmask 1 -> frequencies)

* **sent:** `scan 1000000 2000000 11 1`
* **raw return:**

  ```
  b'1000000 \r\n1100000 \r\n1200000 \r\n1300000 \r\n1400000 \r\n1500000 \r\n1600000 \r\n1700000 \r\n1800000 \r\n1900000 \r\n2000000 '
  ```

## `scan 1000000 2000000 11 2`  (scan outmask 2 -> S11 pairs)

* **sent:** `scan 1000000 2000000 11 2`
* **raw return:**

  ```
  b'1.099591 1.187207 \r\n1.153736 1.298168 \r\n1.233284 1.402242 \r\n1.325617 1.493998 \r\n1.434978 1.563524 \r\n1.561850 1.600860 \r\n1.693943 1.613622 \r\n1.827520 1.587306 \r\n1.948617 1.523846 \r\n2.044666 1.430416 \r\n2.115497 1.320012 '
  ```

## `scan 1000000 2000000 11 6`  (scan outmask 6 -> S11+S21)

* **sent:** `scan 1000000 2000000 11 6`
* **raw return:**

  ```
  b'1.099788 1.188237 -0.000034 0.000128 \r\n1.154678 1.299212 -0.000111 -0.000077 \r\n1.230305 1.404543 0.000047 -0.000044 \r\n1.323817 1.492140 -0.000018 0.000009 \r\n1.432806 1.564259 0.000163 -0.000031 \r\n1.56 ... '78 \r\n1.691253 1.613486 -0.000073 -0.000097 \r\n1.827190 1.583090 0.000044 0.000008 \r\n1.946547 1.521080 -0.000148 -0.000010 \r\n2.042640 1.429340 0.000033 -0.000007 \r\n2.110708 1.322315 -0.000023 -0.000226 '  (total 429 bytes)
  ```

## `scan 1000000 2000000 11 7`  (scan outmask 7 -> freq+S11+S21)

* **sent:** `scan 1000000 2000000 11 7`
* **raw return:**

  ```
  b'1000000 1.099594 1.186013 -0.000046 -0.000065 \r\n1100000 1.156925 1.299160 -0.000006 -0.000023 \r\n1200000 1.230257 1.403737 0.000079 -0.000022 \r\n1300000 1.325828 1.494018 0.000051 -0.000055 \r\n1400000 1. ... '0.000132 \r\n1700000 1.828786 1.587299 -0.000096 -0.000208 \r\n1800000 1.953220 1.517652 0.000052 -0.000048 \r\n1900000 2.042291 1.432723 -0.000070 -0.000164 \r\n2000000 2.109906 1.316657 -0.000223 -0.000071 '  (total 521 bytes)
  ```

## `frequencies`  (freqs from last sweep)

* **sent:** `frequencies`
* **raw return:**

  ```
  b'1000000\r\n1100000\r\n1200000\r\n1300000\r\n1400000\r\n1500000\r\n1600000\r\n1700000\r\n1800000\r\n1900000\r\n2000000'
  ```

## `scan 1000000 2000000 999 2`  (over-max points (error string))

* **sent:** `scan 1000000 2000000 999 2`
* **raw return:**

  ```
  b'sweep points exceeds range 11 -201'
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
```
