with open('D:\\protofolo projectzzz\\ragparser\\frontend\\src\\app\\uploader.tsx', 'r') as f:
    content = f.read()
idx = content.find('"Parse PDF"')
if idx >= 0:
    print(f'Found at index {idx}')
    start = max(0, idx - 50)
    end = min(len(content), idx + 50)
    print(content[start:end])
else:
    print('Not found')
    lines = content.split('\n')
    for i, line in enumerate(lines[110:125], 111):
        print(f'{i}: {line[:60]}')