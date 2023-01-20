# prox-checker
**Async python proxy checker**


### Features
- **Works in 2023**
- **No pycurl needed**, OS independent
- **HTTP, Socks4, Socks5**
- **Async**
- **Fast** (<= 1.5kb per check)
- Checks **availability** and **anonymity**
- **Secure**, no data collecting
- **Typed**


## Installation
`pip install prox-checker`

## Usage
```python
...

from prox_checker import ProxyChecker, ProxyProtocol, ProxyCheckerResult


async def check_my_proxies():
    proxies = [
        '144.24.207.98:8080',
        '103.169.130.51:5678',
        '198.58.126.147:51576',
        '45.79.155.9:3128',
        '206.220.175.2:4145',
    ]

    working_proxies: List[ProxyCheckerResult] = await ProxyChecker().check_proxies(
        proxies=proxies,
        proxy_async_limit=1_000,
        protocol_async_limit=3,
        response_timeout=5,
    )

    print(working_proxies)
    '''
    Output: 
    [
        <ProxyCheckerResult url=http://144.24.207.98:8080 proxy=144.24.207.98:8080 protocol=ProxyProtocol.http>, 
        <ProxyCheckerResult url=socks4://198.58.126.147:51576 proxy=198.58.126.147:51576 protocol=ProxyProtocol.socks4>, 
        <ProxyCheckerResult url=socks5://198.58.126.147:51576 proxy=198.58.126.147:51576 protocol=ProxyProtocol.socks5>,
        <ProxyCheckerResult url=socks4://206.220.175.2:4145 proxy=206.220.175.2:4145 protocol=ProxyProtocol.socks4>, 
        <ProxyCheckerResult url=socks5://206.220.175.2:4145 proxy=206.220.175.2:4145 protocol=ProxyProtocol.socks5>
    ]
    
    Leaves only anon working proxies, separated by protocols
    '''
    socks5_urls = [
        result.url
        for result in working_proxies
        if result.protocol == ProxyProtocol.socks5
    ]
    print(socks5_urls)  # ['socks5://198.58.126.147:51576', 'socks5://206.220.175.2:4145']

    max_bandwidth_bytes_s = ProxyChecker.estimate_max_bandwidth_bytes_s(
        proxy_async_limit=1_000,
        protocol_async_limit=3,
    )
    max_bandwidth_mb_s = max_bandwidth_bytes_s / 1024 / 1024
    print(max_bandwidth_mb_s)  # 4.39453125

    custom_judges = [
        'http://proxyjudge.us',
        'http://azenv.net/',
    ]
    custom_judges_working_proxies = await ProxyChecker(judges=custom_judges).check_proxies(
        proxies=proxies,
        proxy_async_limit=1_000,
        protocol_async_limit=3,
        response_timeout=5,
    )
    print(custom_judges_working_proxies)  # same as first

...

```