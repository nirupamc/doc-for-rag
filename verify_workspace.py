with open('D:\\protofolo projectzzz\\ragparser\\frontend\\src\\app\\workspace.tsx', 'r') as f:
    content = f.read()
open_parens = sum(1 for c in content if c == '(')
close_parens = sum(1 for c in content if c == ')')
print(f'Open parens: {open_parens}, Close parens: {close_parens}')

import re
summary_count = len(re.findall(r'view === "summary"', content))
export_count = len(re.findall(r'view === "export"', content))
print(f'view === summary: {summary_count}')
print(f'view === export: {export_count}')