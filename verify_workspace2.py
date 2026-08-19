with open('D:\\protofolo projectzzz\\ragparser\\frontend\\src\\app\\workspace.tsx', 'r') as f:
    content = f.read()
print('MODE // found:', 'MODE //' in content)
print('01 SUMMARY found:', '01 SUMMARY' in content)
print('02 INSPECT found:', '02 INSPECT' in content)
print('03 EXPORT found:', '03 EXPORT' in content)
print('view === export found:', 'view === "export"' in content)