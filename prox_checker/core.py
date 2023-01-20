import asyncio
import random
from enum import Enum
from typing import Optional, List, Dict, Any, Union, Coroutine, Tuple

import requests
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup


async def gather_limited(
    tasks: List[Coroutine],
    limit: int,
) -> List[Any]:
    def bunch(tasks_list: List[Coroutine]) -> Tuple[List[Coroutine], List[Coroutine]]:
        tasks_bunch = []
        while True:
            if len(tasks_list) == 0:
                break
            task = tasks_list[0]
            tasks_bunch.append(task)
            tasks_list = tasks_list[1:]
            if len(tasks_bunch) >= limit:
                break
        return tasks_bunch, tasks_list

    results = []
    tasks_bunch, tasks_list = bunch(tasks)
    while True:
        if len(tasks_bunch) == 0 and len(tasks_list) == 0:
            break
        results += list(await asyncio.gather(*tasks_bunch))
        tasks_bunch, tasks_list = bunch(tasks_list)

    return results


class ProxyProtocol(Enum):
    http = 'http'
    socks4 = 'socks4'
    socks5 = 'socks5'


class ProxyCheckerResult:

    def __init__(
        self,
        proxy: str,
        protocol: ProxyProtocol,
    ):
        self.proxy = proxy
        self.protocol = protocol

    @property
    def protocol_str(self) -> str:
        return str(self.protocol.value)

    @property
    def url(self) -> str:
        return f'{self.protocol_str}://{self.proxy}'

    def __repr__(self):
        return f'<{self.__class__.__name__} url={self.url} proxy={self.proxy} protocol={self.protocol}>'


class ProxyChecker:
    judges = [
        'http://proxyjudge.us',
        'http://azenv.net/',
        'http://httpheader.net/azenv.php',
        'http://mojeip.net.pl/asdfa/azenv.php'
    ]

    def __init__(self, judges: Optional[List[str]] = None):
        if judges is None or len(judges) == 0:
            judges = self.__class__.judges
        self.judges = [
            judge
            for judge in judges
            if requests.get(judge).status_code == 200
        ]

    @property
    def random_judge(self):
        return random.choice(self.judges)

    def get_normal_ip(self) -> str:
        text = requests.get(self.random_judge).text
        lines = BeautifulSoup(text, features='html.parser').select_one('pre').get_text().splitlines()
        data = {}
        for line in lines:
            if '=' in line:
                k, v = line.split('=')
                data[k.strip()] = v.strip()
        return data['REMOTE_ADDR']

    async def check_proxy(
        self,
        proxy: str,
        real_ip: str,
        protocol: ProxyProtocol = ProxyProtocol.http,
        response_timeout: int = 5,
    ) -> bool:
        try:
            connector = ProxyConnector.from_url(f'{protocol.value}://{proxy}')
            async with ClientSession(connector=connector) as session:
                async with session.get(self.random_judge, timeout=response_timeout) as response:
                    text = await response.text()
                    if response.status == 200 and not (real_ip in text):
                        return True
        except BaseException as ex:
            pass
        return False

    async def check_proxy_any_protocol(
        self,
        proxy: str,
        real_ip: str,
        protocol_async_limit: int = 3,
        response_timeout: int = 5,
    ) -> List[ProxyCheckerResult]:
        results: List[ProxyCheckerResult] = []
        protocols = [p for p in ProxyProtocol]
        responses: List[bool] = await gather_limited([
            self.check_proxy(
                proxy=proxy,
                real_ip=real_ip,
                response_timeout=response_timeout,
                protocol=protocol,
            )
            for protocol in protocols
        ], limit=protocol_async_limit)
        for i, success in enumerate(responses):
            protocol = protocols[i]
            if success:
                results.append(ProxyCheckerResult(
                    proxy=proxy,
                    protocol=protocol,
                ))
        return results

    async def check_proxies(
        self,
        proxies: List[str],
        proxy_async_limit: int = 1_000,
        protocol_async_limit: int = 3,
        response_timeout: int = 5,
    ) -> List[ProxyCheckerResult]:

        ip = self.get_normal_ip()

        proxies_info: List[List[ProxyCheckerResult]] = await gather_limited(
            [
                self.check_proxy_any_protocol(
                    proxy=proxy,
                    real_ip=ip,
                    response_timeout=response_timeout,
                    protocol_async_limit=protocol_async_limit,
                )
                for proxy in proxies
            ], limit=proxy_async_limit
        )

        result_proxies_info = []
        for proxy_info in proxies_info:
            for protocol_proxy_info in proxy_info:
                result_proxies_info.append(protocol_proxy_info)

        return result_proxies_info

    @classmethod
    def estimate_max_bandwidth_bytes_s(
        cls,
        proxy_async_limit: int = 1_000,
        protocol_async_limit: int = 3,
    ) -> int:
        MAX_RESPONSE_SIZE = 1.5*1024  # 1.5kb
        return MAX_RESPONSE_SIZE*proxy_async_limit*protocol_async_limit

