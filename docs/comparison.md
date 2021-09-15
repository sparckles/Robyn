# Performance comparison across different frameworks

## Read this before you scroll down

The comparison is not meant to defame any of the of the developers or the frameworks listed below. The names of the frameworks have been listed for a clear comparison. All of these frameworks are the reason for me having a high inclination towards the python web ecosystem and I hope to have not caused any offence( to anyone) by listing these frameworks.

**Also, these tests were done on my development machine and the numbers portrayed below are not absolute by any means. These numbers only indicate the relative performance of these frameworks.**

I used [oha](https://github.com/hatoo/oha) to perform the testing of 10000 requests on the following frameworks and the results were as follows:

1. Flask(Gunicorn)
```
  Total:	11.7603 secs
  Slowest:	0.0777 secs
  Fastest:	0.0052 secs
  Average:	0.0586 secs
  Requests/sec:	850.3200
```
2. FastAPI(Uvicorn)
```
  Total:	12.4052 secs
  Slowest:	0.1302 secs
  Fastest:	0.0227 secs
  Average:	0.0619 secs
  Requests/sec:	806.1105
```
3. Django(Gunicron)
```
  Success rate:	1.0000
  Total:	24.9545 secs
  Slowest:	0.1587 secs
  Fastest:	0.0168 secs
  Average:	0.1245 secs
  Requests/sec:	400.7296
```
4. Robyn(Doesn't need a *SGI)
```
  Total:	1.8324 secs
  Slowest:	0.0269 secs
  Fastest:	0.0024 secs
  Average:	0.0091 secs
  Requests/sec:	5457.2339
```

Robyn is able to serve the 10k requests in 1.8 seconds followed by Flask and FastAPI, which take around 12 seconds. Finally, Django takes around 24 seconds.

## Verbose Logs
Flask(Gunicorn)
```
Summary:
  Success rate:	1.0000
  Total:	11.7603 secs
  Slowest:	0.0777 secs
  Fastest:	0.0052 secs
  Average:	0.0586 secs
  Requests/sec:	850.3200

  Total data:	126.95 KiB
  Size/request:	13 B
  Size/sec:	10.79 KiB

Response time histogram:
  0.007 [4]    |
  0.013 [6]    |
  0.020 [5]    |
  0.026 [3]    |
  0.033 [4]    |
  0.040 [5]    |
  0.046 [6]    |
  0.053 [3855] |■■■■■■■■■■■■■■■■■■■■
  0.059 [5928] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.066 [136]  |
  0.072 [48]   |

Latency distribution:
  10% in 0.0559 secs
  25% in 0.0572 secs
  50% in 0.0585 secs
  75% in 0.0599 secs
  90% in 0.0616 secs
  95% in 0.0629 secs
  99% in 0.0658 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0002 secs, 0.0001 secs, 0.0077 secs
  DNS-lookup:	0.0000 secs, 0.0000 secs, 0.0007 secs

Status code distribution:
  [200] 10000 responses
```

FastAPI(Uvicorn)
```
Summary:
  Success rate:	1.0000
  Total:	12.4052 secs
  Slowest:	0.1302 secs
  Fastest:	0.0227 secs
  Average:	0.0619 secs
  Requests/sec:	806.1105

  Total data:	166.02 KiB
  Size/request:	17 B
  Size/sec:	13.38 KiB

Response time histogram:
  0.010 [192]  |■
  0.020 [819]  |■■■■■■■
  0.029 [308]  |■■
  0.039 [3698] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.049 [3678] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.059 [452]  |■■■
  0.068 [327]  |■■
  0.078 [385]  |■■■
  0.088 [110]  |
  0.098 [29]   |
  0.108 [2]    |

Latency distribution:
  10% in 0.0397 secs
  25% in 0.0568 secs
  50% in 0.0618 secs
  75% in 0.0663 secs
  90% in 0.0770 secs
  95% in 0.0919 secs
  99% in 0.1026 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0028 secs, 0.0026 secs, 0.0032 secs
  DNS-lookup:	0.0000 secs, 0.0000 secs, 0.0002 secs

Status code distribution:
  [200] 10000 responses
```

Robyn
```
Summary:
  Success rate:	1.0000
  Total:	1.8324 secs
  Slowest:	0.0269 secs
  Fastest:	0.0024 secs
  Average:	0.0091 secs
  Requests/sec:	5457.2339

  Total data:	117.19 KiB
  Size/request:	12 B
  Size/sec:	63.95 KiB

Response time histogram:
  0.002 [183]  |■
  0.004 [1669] |■■■■■■■■■■■■■■
  0.007 [3724] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.009 [2631] |■■■■■■■■■■■■■■■■■■■■■■
  0.011 [1060] |■■■■■■■■■
  0.013 [496]  |■■■■
  0.016 [188]  |■
  0.018 [34]   |
  0.020 [12]   |
  0.022 [2]    |
  0.025 [1]    |

Latency distribution:
  10% in 0.0061 secs
  25% in 0.0073 secs
  50% in 0.0087 secs
  75% in 0.0105 secs
  90% in 0.0129 secs
  95% in 0.0143 secs
  99% in 0.0171 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0049 secs, 0.0035 secs, 0.0065 secs
  DNS-lookup:	0.0001 secs, 0.0000 secs, 0.0010 secs

Status code distribution:
  [200] 10000 responses
```

Django(Gunicorn)
```
Summary:
  Success rate:	1.0000
  Total:	24.9545 secs
  Slowest:	0.1587 secs
  Fastest:	0.0168 secs
  Average:	0.1245 secs
  Requests/sec:	400.7296

  Total data:	102.01 MiB
  Size/request:	10.45 KiB
  Size/sec:	4.09 MiB

Response time histogram:
  0.013 [5]    |
  0.026 [5]    |
  0.039 [4]    |
  0.052 [3]    |
  0.064 [5]    |
  0.077 [5]    |
  0.090 [5]    |
  0.103 [213]  |
  0.116 [9578] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.129 [172]  |
  0.142 [5]    |

Latency distribution:
  10% in 0.1214 secs
  25% in 0.1226 secs
  50% in 0.1243 secs
  75% in 0.1262 secs
  90% in 0.1282 secs
  95% in 0.1297 secs
  99% in 0.1355 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0002 secs, 0.0001 secs, 0.0092 secs
  DNS-lookup:	0.0000 secs, 0.0000 secs, 0.0004 secs

Status code distribution:
  [200] 10000 responses
```


