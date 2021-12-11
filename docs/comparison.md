# Performance comparison across different frameworks

## Read this before you scroll down

The comparison is not meant to defame any of the of the developers or the frameworks listed below. The names of the frameworks have been listed for a clear comparison. All of these frameworks are the reason for me having a high inclination towards the python web ecosystem and I hope to have not caused any offence (to anyone) by listing these frameworks.

**Also, these tests were done on my development machine and the numbers portrayed below are not absolute by any means. These numbers only indicate the relative performance of these frameworks.**

I used [oha](https://github.com/hatoo/oha) to perform the testing of 10000 requests on the following frameworks and the results were as follows:

1. Flask(Gunicorn)
```
  Total:        5.5254 secs
  Slowest:      0.0784 secs
  Fastest:      0.0028 secs
  Average:      0.0275 secs
  Requests/sec: 1809.8082
```

2. FastAPI(Uvicorn)
```
  Total:        4.1314 secs
  Slowest:      0.0733 secs
  Fastest:      0.0027 secs
  Average:      0.0206 secs
  Requests/sec: 2420.4851
```
3. Django(Gunicorn)
```
  Total:        13.5070 secs
  Slowest:      0.3635 secs
  Fastest:      0.0249 secs
  Average:      0.0674 secs
  Requests/sec: 740.3558
```
4. Robyn(Doesn't need a *SGI)
```
  Total:	1.8324 secs
  Slowest:	0.0269 secs
  Fastest:	0.0024 secs
  Average:	0.0091 secs
  Requests/sec:	5457.2339
```

4. Robyn (5 workers)
```
  Total:	1.5592 secs
  Slowest:	0.0211 secs
  Fastest:	0.0017 secs
  Average:	0.0078 secs
  Requests/sec:	6413.6480
```

Robyn is able to serve the 10k requests in 1.8 seconds followed by Flask and FastAPI, which take around 5 seconds(using 5 workers on a dual core machine). Finally, Django takes around 13.5070 seconds.

## Verbose Logs
Flask(Gunicorn)
```
Summary:
  Success rate: 1.0000
  Total:        5.5254 secs
  Slowest:      0.0784 secs
  Fastest:      0.0028 secs
  Average:      0.0275 secs
  Requests/sec: 1809.8082

  Total data:   126.95 KiB
  Size/request: 13 B
  Size/sec:     22.98 KiB

Response time histogram:
  0.007 [55]   |
  0.014 [641]  |■■■■■
  0.021 [2413] |■■■■■■■■■■■■■■■■■■■■
  0.027 [3771] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.034 [1999] |■■■■■■■■■■■■■■■■
  0.041 [737]  |■■■■■■
  0.048 [236]  |■■
  0.055 [75]   |
  0.062 [46]   |
  0.069 [24]   |
  0.076 [3]    |

Latency distribution:
  10% in 0.0178 secs
  25% in 0.0223 secs
  50% in 0.0266 secs
  75% in 0.0317 secs
  90% in 0.0378 secs
  95% in 0.0419 secs
  99% in 0.0551 secs

Details (average, fastest, slowest):
  DNS+dialup:   0.0071 secs, 0.0001 secs, 0.0443 secs
  DNS-lookup:   0.0000 secs, 0.0000 secs, 0.0010 secs

Status code distribution:
  [200] 10000 responses
```

FastAPI(Uvicorn)
```
Summary:
  Success rate: 1.0000
  Total:        4.1314 secs
  Slowest:      0.0733 secs
  Fastest:      0.0027 secs
  Average:      0.0206 secs
  Requests/sec: 2420.4851

  Total data:   166.02 KiB
  Size/request: 17 B
  Size/sec:     40.18 KiB

Response time histogram:
  0.005 [175]  |■
  0.011 [1541] |■■■■■■■■■■■■■■■■
  0.016 [2942] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.021 [2770] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.027 [1479] |■■■■■■■■■■■■■■■■
  0.032 [608]  |■■■■■■
  0.038 [217]  |■■
  0.043 [103]  |■
  0.048 [53]   |
  0.054 [54]   |
  0.059 [58]   |

Latency distribution:
  10% in 0.0120 secs
  25% in 0.0151 secs
  50% in 0.0194 secs
  75% in 0.0243 secs
  90% in 0.0300 secs
  95% in 0.0348 secs
  99% in 0.0522 secs

Details (average, fastest, slowest):
  DNS+dialup:   0.0088 secs, 0.0073 secs, 0.0103 secs
  DNS-lookup:   0.0001 secs, 0.0000 secs, 0.0008 secs

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
  Success rate: 1.0000
  Total:        13.5070 secs
  Slowest:      0.3635 secs
  Fastest:      0.0249 secs
  Average:      0.0674 secs
  Requests/sec: 740.3558

  Total data:   102.01 MiB
  Size/request: 10.45 KiB
  Size/sec:     7.55 MiB

Response time histogram:
  0.016 [283]  |■
  0.032 [2616] |■■■■■■■■■■■■■■■■■■
  0.048 [4587] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.064 [1829] |■■■■■■■■■■■■
  0.081 [362]  |■■
  0.097 [98]   |
  0.113 [105]  |
  0.129 [20]   |
  0.145 [7]    |
  0.161 [28]   |
  0.177 [65]   |

Latency distribution:
  10% in 0.0493 secs
  25% in 0.0559 secs
  50% in 0.0638 secs
  75% in 0.0733 secs
  90% in 0.0840 secs
  95% in 0.0948 secs
  99% in 0.1543 secs

Details (average, fastest, slowest):
  DNS+dialup:   0.0097 secs, 0.0001 secs, 0.0444 secs
  DNS-lookup:   0.0000 secs, 0.0000 secs, 0.0007 secs

Status code distribution:
  [200] 10000 responses
```


Robyn(with 5 workers)
```
Summary:
  Success rate:	1.0000
  Total:	1.5592 secs
  Slowest:	0.0211 secs
  Fastest:	0.0017 secs
  Average:	0.0078 secs
  Requests/sec:	6413.6480

  Total data:	126.95 KiB
  Size/request:	13 B
  Size/sec:	81.42 KiB

Response time histogram:
  0.002 [30]   |
  0.004 [599]  |■■■■■
  0.005 [3336] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.007 [3309] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.009 [1614] |■■■■■■■■■■■■■■■
  0.011 [749]  |■■■■■■■
  0.012 [253]  |■■
  0.014 [94]   |
  0.016 [14]   |
  0.018 [1]    |
  0.019 [1]    |

Latency distribution:
  10% in 0.0055 secs
  25% in 0.0063 secs
  50% in 0.0074 secs
  75% in 0.0089 secs
  90% in 0.0107 secs
  95% in 0.0117 secs
  99% in 0.0142 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0022 secs, 0.0013 secs, 0.0028 secs
  DNS-lookup:	0.0000 secs, 0.0000 secs, 0.0001 secs

Status code distribution:
  [200] 10000 responses
```
