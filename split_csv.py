import pandas as pd
import glob

# 폴더 내 NASA 원본 CSV 파일 자동 탐색
file_paths = glob.glob("PS_*.csv")
if not file_paths:
    file_paths = glob.glob("*.csv")

if file_paths:
    file_path = file_paths[0]
    print(f"'{file_path}' 파일 분할을 시작합니다...")
    
    # 필요한 핵심 컬럼만 골라서 메모리 아끼기
    needed_cols = [
        'hostname', 'pl_name', 'st_lum', 'st_mass', 'st_spectype',
        'discoverymethod', 'sy_pnum', 'pl_orbsmax', 'pl_orbeccen',
        'pl_rade', 'pl_bmasse', 'pl_eqt'
    ]
    
    df = pd.read_csv(file_path, comment='#', usecols=lambda c: c in needed_cols, low_memory=False)
    
    # 항성 이름 첫 글자 기준으로 5개 그룹으로 나누기
    df['first_letter'] = df['hostname'].astype(str).str[0].str.upper()
    
    def get_group(char):
        if 'A' <= char <= 'E': return 'nasa_part1.csv'
        elif 'F' <= char <= 'J': return 'nasa_part2.csv'
        elif 'K' <= char <= 'O': return 'nasa_part3.csv'
        elif 'P' <= char <= 'T': return 'nasa_part4.csv'
        else: return 'nasa_part5.csv'

    df['group_file'] = df['first_letter'].apply(get_group)
    
    for filename, group_df in df.groupby('group_file'):
        out_df = group_df.drop(columns=['first_letter', 'group_file'])
        out_df.to_csv(filename, index=False)
        print(f"생성됨: {filename} (행성 수: {len(out_df)}개)")
        
    print("모든 파일 분할 완료!")
else:
    print("CSV 파일을 찾지 못했습니다.")
