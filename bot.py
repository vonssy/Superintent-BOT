from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from curl_cffi import requests
from fake_useragent import FakeUserAgent
from http.cookies import SimpleCookie
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from datetime import datetime, timezone
from colorama import *
import asyncio, json, re, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class SuperIntent:
    def __init__(self) -> None:
        self.BASE_API = "https://bff-root.superintent.ai/v1"
        self.REF_CODE = "PZQB8wXy0k" # U can change it with yours.
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.cookie_headers = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}SuperIntent {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
        
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address

            return address
        except Exception as e:
            return None
    
    def generate_payload(self, account: str, address: str, nonce: str):
        try:
            timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            message = f"mission.superintent.ai wants you to sign in with your Ethereum account:\n{address}\n\nTo securely sign in, please sign this message to verify you're the owner of this wallet.\n\nURI: https://mission.superintent.ai\nVersion: 1\nChain ID: 1\nNonce: {nonce}\nIssued At: {timestamp}"
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)

            return {
                "message": message,
                "signature": signature
            }
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")

    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "With" if proxy_choice == 1 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        rotate_proxy = False
        if proxy_choice == 1:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate_proxy in ["y", "n"]:
                    rotate_proxy = rotate_proxy == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return proxy_choice, rotate_proxy
    
    async def check_connection(self, proxy_url=None):
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        try:
            response = await asyncio.to_thread(requests.get, url="https://api.ipify.org?format=json", proxies=proxies, timeout=30, impersonate="chrome120")
            response.raise_for_status()
            return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def auth_nonce(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/auth/nonce"
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.get, url=url, headers=self.HEADERS[address], proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()
                result = response.json()

                raw_cookies = response.headers.get_list('Set-Cookie')
                if raw_cookies:
                    cookie = SimpleCookie()
                    cookie.load("\n".join(raw_cookies))
                    cookie_string = "; ".join([f"{key}={morsel.value}" for key, morsel in cookie.items()])
                    self.cookie_headers[address] = cookie_string

                    return result
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch Nonce Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_siwe(self, account: str, address: str, nonce: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/auth/siwe"
        data = json.dumps(self.generate_payload(account, address, nonce))
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.post, url=url, headers=headers, data=data, proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()

                raw_cookies = response.headers.get_list('Set-Cookie')
                if raw_cookies:
                    cookie = SimpleCookie()
                    cookie.load("\n".join(raw_cookies))
                    cookie_string = "; ".join([f"{key}={morsel.value}" for key, morsel in cookie.items()])
                    self.cookie_headers[address] = cookie_string

                    return True
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def bind_referral(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/me/referral/bind"
        data = json.dumps({"referralCode": self.REF_CODE})
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.post, url=url, headers=headers, data=data, proxies=proxies, timeout=120, impersonate="chrome120")
                if response.status_code == 400: return None
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Bind Referral Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_me(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/auth/me"
        headers = {
            **self.HEADERS[address],
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.get, url=url, headers=headers, proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Onboarding:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch Status Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def complete_onboarding(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/onboarding/complete"
        data = json.dumps({"signal": {}})
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.post, url=url, headers=headers, data=data, proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Onboarding:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Completed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def user_stats(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/me/stats"
        headers = {
            **self.HEADERS[address],
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.get, url=url, headers=headers, proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Points    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch PTS Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
    
    async def checkin_status(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/check-in/status"
        headers = {
            **self.HEADERS[address],
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.get, url=url, headers=headers, proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch Status Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def claim_checkin(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/check-in"
        headers = {
            **self.HEADERS[address],
            "Content-Length": "0",
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.post, url=url, headers=headers, proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def quest_lists(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/quests"
        headers = {
            **self.HEADERS[address],
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.get, url=url, headers=headers, proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Task Lists:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch Lists Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def quest_progress(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/quests/progress"
        headers = {
            **self.HEADERS[address],
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.get, url=url, headers=headers, proxies=proxies, timeout=120, impersonate="chrome120")
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Task Lists:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Fetch Progress Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def verify_quest(self, address: str, quest_id: str, quest_name: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/quests/verify"
        data = json.dumps({"id": quest_id})
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "Cookie": self.cookie_headers[address]
        }
        for attempt in range(retries):
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            try:
                response = await asyncio.to_thread(requests.post, url=url, headers=headers, data=data, proxies=proxies, timeout=120, impersonate="chrome120")
                if response.status_code in [400, 429]:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}   > {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{quest_name}{Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                    )
                    return None
                response.raise_for_status()
                return response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   > {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{quest_name}{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    await asyncio.sleep(1)
                    continue

                return False

            return True
    
    async def process_user_login(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            auth_nonce = await self.auth_nonce(address, proxy)
            if not auth_nonce: return

            nonce = auth_nonce.get("nonce")

            auth_verify = await self.auth_siwe(account, address, nonce, proxy)
            if not auth_verify: return False

            self.cookie_headers[address] = self.cookie_headers[address] + f"; l-addr={address}"

            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.GREEN + Style.BRIGHT} Login Success {Style.RESET_ALL}"
            )

            await self.bind_referral(address, proxy)

            return True

    async def process_accounts(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        logined = await self.process_user_login(account, address, use_proxy, rotate_proxy)
        if logined:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            user = await self.auth_me(address, proxy)
            if user:
                is_onboarded = user.get("onboardingCompleted")

                if not is_onboarded:
                    complete = await self.complete_onboarding(address, proxy)
                    if complete:
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}Onboarding:{Style.RESET_ALL}"
                            f"{Fore.GREEN + Style.BRIGHT} Completed {Style.RESET_ALL}"
                        )
                else:
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Onboarding:{Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                    )

            stats = await self.user_stats(address, proxy)
            if stats:
                points = stats.get("totalPoints", 0)

                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Points    :{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} {points} PTS {Style.RESET_ALL}"
                )

            checkin = await self.checkin_status(address, proxy)
            if checkin:
                has_checkin = checkin.get("hasCheckedInToday", False)

                if not has_checkin:
                    claim = await self.claim_checkin(address, proxy)
                    if claim:
                        reward = claim.get("pointsGranted")

                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}Check-In  :{Style.RESET_ALL}"
                            f"{Fore.GREEN + Style.BRIGHT} Claimed Successfully {Style.RESET_ALL}"
                            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT} Reward: {Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT}{reward} PTS{Style.RESET_ALL}"
                        )

                else:
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Check-In  :{Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                    )

            quest_lists = await self.quest_lists(address, proxy)
            if quest_lists:

                quest_progress = await self.quest_progress(address, proxy)
                if quest_progress is None: return

                self.log(f"{Fore.CYAN + Style.BRIGHT}Task Lists:{Style.RESET_ALL}")

                for quest in quest_lists:
                    quest_id = quest.get("id")
                    quest_name = quest.get("name")
                    quest_reward = quest.get("points")

                    is_completed = False

                    for progress in quest_progress:
                        if progress.get("id") == quest_id and progress.get("completed"):
                            is_completed = True
                            break

                    if is_completed:
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}   > {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{quest_name}{Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                        )
                        continue

                    verify = await self.verify_quest(address, quest_id, quest_name, proxy)
                    if verify:
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}   > {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{quest_name}{Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT} Completed {Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT} Reward: {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{quest_reward} PTS{Style.RESET_ALL}"
                        )

                    await asyncio.sleep(1)

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            proxy_choice, rotate_proxy = self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                use_proxy = True if proxy_choice == 1 else False
                if use_proxy:
                    await self.load_proxies()

                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status    :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue

                        self.HEADERS[address] = {
                            "Accept": "application/json, text/plain, */*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://mission.superintent.ai",
                            "Referer": "https://mission.superintent.ai/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "User-Agent": FakeUserAgent().random
                        }
                        
                        await self.process_accounts(account, address, use_proxy, rotate_proxy)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                
                delay = 24 * 60 * 60
                while delay > 0:
                    formatted_time = self.format_seconds(delay)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)
                    delay -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = SuperIntent()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] SuperIntent - BOT{Style.RESET_ALL}                                       "                              
        )