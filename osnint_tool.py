import os
import sys
import warnings
import re
from ddgs import DDGS
from colorama import Fore, Style, init

warnings.filterwarnings("ignore")
init(autoreset=True)

def ask_embedded_ai(system_context, user_prompt, is_deep=False):
    """Executes local inference with dynamic response length optimization"""
    try:
        from llama_cpp import Llama
        
        # FIXED: Upgraded repository and filename to the 3B model architecture (~1.9GB)
        llm = Llama.from_pretrained(
            repo_id="Qwen/Qwen2.5-3B-Instruct-GGUF",
            filename="qwen2.5-3b-instruct-q4_k_m.gguf",
            verbose=False,
            n_ctx=4048
        )
        
        formatted_prompt = f"<|im_start|>system\n{system_context}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        # Give the AI more generation space if deep mode scaling is high
        max_tokens = 1024 if is_deep else 512
        
        output = llm(
            formatted_prompt, 
            max_tokens=max_tokens, 
            temperature=0.1, 
            repeat_penalty=1.2,
            frequency_penalty=0.4,
            stop=["<|im_end|>"], 
            echo=False
        )
        
        if isinstance(output, dict):
            if 'choices' in output and isinstance(output['choices'], list) and len(output['choices']) > 0:
                choice = output['choices'][0]
                if isinstance(choice, dict) and 'text' in choice:
                    return choice['text'].strip()
        return str(output)
    except Exception as e:
        return f"AI Engine Error: {e}"

def execute_recon(mode_label, system_instructions, search_query, crawl_depth):
    is_deep = crawl_depth > 5
    depth_tag = f"{Fore.RED}DEEP-SCAN ({crawl_depth} Sources){Style.RESET_ALL}" if is_deep else "STANDARD"
    
    print(f"\n[{Fore.BLUE}*{Style.RESET_ALL}] [{depth_tag}] Crawling public web...")
    
    search_results = []
    try:
        with DDGS() as ddgs:
            # Dynamically uses the custom crawl_depth integer
            results = ddgs.text(search_query, max_results=crawl_depth)
            if results:
                for r in results:
                    search_results.append(f"Source: {r['href']}\nTitle: {r['title']}\nData: {r['body']}\n---")
    except Exception as e:
        print(f"[{Fore.RED}!{Style.RESET_ALL}] Search module warning: {e}")

    raw_context = "\n".join(search_results) if search_results else "No records found on the public web."
    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Syncing footprint data with local AI context matrix...")

    full_ai_prompt = f"Target Query: {search_query}\n\nWeb Intelligence Retrieved:\n{raw_context}\n\nPerform objective analysis."
    report = ask_embedded_ai(system_instructions, full_ai_prompt, is_deep=is_deep)
    
    print(f"\n{Fore.CYAN}--- OSNINT REPORT: {mode_label} (DEPTH: {crawl_depth}) ---")
    print(Fore.WHITE + report)
    print(f"{Fore.CYAN}-----------------------------------\n")

    try:
        filename = f"report_depth{crawl_depth}_{mode_label.lower()}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"OSNINT REPORT\nMode: {mode_label}\nCrawl Depth: {crawl_depth}\nTarget: {search_query}\n\n{report}")
        print(f"[{Fore.GREEN}+{Style.RESET_ALL}] Saved report to: {Fore.YELLOW}{filename}")
    except Exception:
        pass

def show_help():
    print(f"\n{Fore.CYAN}Available Field Commands:")
    print(f"  {Fore.YELLOW}/investigate {Fore.WHITE}<Prompt>   - Cross-reference mixed targets (names + locations)")
    print(f"  {Fore.YELLOW}/name {Fore.WHITE}<Full Name>       - Search for personal/corporate records")
    print(f"  {Fore.YELLOW}/user {Fore.WHITE}<Username>        - Search for online profiles and handles")
    print(f"  {Fore.YELLOW}/email {Fore.WHITE}<Email>          - Search for linked data leaks or accounts")
    print(f"  {Fore.YELLOW}/domain {Fore.WHITE}<Domain>       - Search for website infrastructure records")
    print(f"\n{Fore.CYAN}Dynamic Depth Modifier:")
    print(f"  Prepend {Fore.RED}<number>>deep-{Fore.WHITE} before any command to set custom source limits.")
    print(f"  Examples:")
    print(f"    {Fore.RED}10>deep-/name {Fore.WHITE}Giuseppe   - Crawls exactly 10 web targets.")
    print(f"    {Fore.RED}25>deep-/user {Fore.WHITE}itzbubi    - Comprehensive check across 25 web targets.")
    print(f"  Default depth without prefix is 5 sources.")
    print(f"  {Fore.YELLOW}/exit                   {Fore.WHITE}- Close the application\n")

if __name__ == "__main__":
    print(Fore.WHITE + "=========================================")
    print(Fore.CYAN + "   OSNINT - Open Source Nano Intelligence")
    print(Fore.WHITE + "=========================================")
    print(f"Type {Fore.YELLOW}/help{Style.RESET_ALL} to see available commands.\n")

    base_directive = "CRITICAL: Never invent background facts. If the web data does not contain clear proof, state 'No verifiable public footprint found.' Do not make assumptions."

    while True:
        try:
            terminal_input = input(f"{Fore.CYAN}osnint{Fore.WHITE} > {Style.RESET_ALL}").strip()
            if not terminal_input:
                continue
            
            if terminal_input.lower() == "/exit":
                print(f"[{Fore.YELLOW}*{Style.RESET_ALL}] Exiting...")
                break
            elif terminal_input.lower() == "/help":
                show_help()
                continue
            
            # Default tracking values
            crawl_depth = 5
            raw_command_string = terminal_input
            
            # REGEX: Check if input starts with a number followed by ">deep-/"
            match = re.match(r"^(\d+)>deep-/", terminal_input.lower())
            if match:
                crawl_depth = int(match.group(1))
                # Ensure safety bounds for depth scaling
                crawl_depth = min(40, max(1, crawl_depth)) 
                # Strip the prefix dynamically (length of number + length of ">deep-")
                prefix_length = len(match.group(1)) + 6
                raw_command_string = terminal_input[prefix_length:]
            # Fallback if user just writes "deep-/" without a number
            elif terminal_input.lower().startswith("deep-/"):
                crawl_depth = 15
                raw_command_string = terminal_input[5:]
                
            if raw_command_string.startswith("/"):
                parts = raw_command_string.split(" ", 1)
                command = parts[0].lower()
                
                if len(parts) < 2:
                    print(f"[{Fore.RED}!{Style.RESET_ALL}] Error: Missing parameters. Usage: {command} <target>")
                    continue
                    
                target_value = parts[1].strip()
                
                # Dynamic system briefing adjustments based on depth
                detail_modifier = "Provide an exhaustive, highly detailed intelligence brief documenting every found metadata point." if crawl_depth > 5 else "Provide a compact summary."
                
                if command == "/investigate":
                    sys_ctx = f"You are a senior intelligence analyst. {base_directive} {detail_modifier} Dissect multi-target inputs and map exact links. Structure: 1. Objective, 2. Verifiable Targets, 3. Interconnection Matrix, 4. Leads."
                    execute_recon("COMPLEX_INVESTIGATION", sys_ctx, target_value, crawl_depth)
                elif command == "/name":
                    sys_ctx = f"You are a corporate intelligence scanner. {base_directive} {detail_modifier} Summarize public records, company ties, and listings. Structure: 1. Profile Summary, 2. Corporate/Financial Ties, 3. Comprehensive Footprint."
                    execute_recon("NAME", sys_ctx, target_value, crawl_depth)
                elif command == "/user":
                    sys_ctx = f"You are an alias tracking analyst. {base_directive} {detail_modifier} Map registered accounts and profiles found for this username. Structure: 1. Handle Overview, 2. Associated Networks & Verification."
                    execute_recon("USERNAME", sys_ctx, target_value, crawl_depth)
                elif command == "/email":
                    sys_ctx = f"You are a privacy audit specialist. {base_directive} {detail_modifier} Map public exposures associated with this email. Structure: 1. Exposure Log, 2. Connected Sources."
                    execute_recon("EMAIL", sys_ctx, target_value, crawl_depth)
                elif command == "/domain":
                    sys_ctx = f"You are a network security officer. {base_directive} {detail_modifier} Document domain infrastructure entries and routing indicators. Structure: 1. Domain Diagnostics, 2. Network Footprint Details."
                    execute_recon("DOMAIN", sys_ctx, target_value, crawl_depth)
                else:
                    print(f"[{Fore.RED}!{Style.RESET_ALL}] Error: Unknown command. Type /help.")
            else:
                print(f"[{Fore.YELLOW}*{Style.RESET_ALL}] Standard search detected. For precise tracking, use specialized commands. Type /help.")
                
        except (KeyboardInterrupt, EOFError):
            print(f"\n[{Fore.YELLOW}*{Style.RESET_ALL}] Canceled. Exiting...")
            break
