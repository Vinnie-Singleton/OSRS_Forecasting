import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import numpy as np
import math
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import os
from time import sleep

wait_time = 300
mins = wait_time//60

hs_info_file_path = 'path\to\file'

issues_file_path = 'path\to\file'

hiscores_file_path = 'path\to\file'

def get_soup(url,page_number):
    full_url = f'{url}{page_number}'
    data = requests.get(full_url)
    soup = bs(data.text, "html.parser")
    return soup

def find_last_page_and_rank(last_known_last_page,url,verbose=True,estimated_growth_rate=0):
    
    def is_first_page(soup):
        content = soup.find('div',{'id':'contentHiscores'})
        page_traversal = content.find('nav',{'class':'personal-hiscores__pagination'})
        imgs = page_traversal.findAll('img')
        for img in imgs:
            if 'Scroll Up' in img['alt']:
                return False
        return True
    
    def is_last_page(soup):
        content = soup.find('div',{'id':'contentHiscores'})
        page_traversal = content.find('nav',{'class':'personal-hiscores__pagination'})
        imgs = page_traversal.findAll('img')
        for img in imgs:
            if 'Scroll Down' in img['alt']:
                return False
        return True
    
    def page_blocked(soup):
        content = soup.find('div',{'id':'contentHiscores'})
        if content:
            return False
        print('Page is blocked')
        return True
    
    def get_last_rank(soup):
        main = soup.find("div", {"id": "contentHiscores"})
        table = main.find("table")
        
        last_person_rank = 0
        
        for person in table.findAll("tr",{"class": "personal-hiscores__row"}):
            rank = int(person("td")[0].text.strip().replace('\n','').replace(',',''))
            
            if rank > last_person_rank:
                last_person_rank = rank
                
        return last_person_rank
    
    def binary_search(low,high,verbose):
        # do a binary search to find the last page

        count = 0

        while low <= high:
            mid = (high + low) // 2
            count += 1
            soup = get_soup(url,mid)

            if page_blocked(soup):
                print('Page is blocked... waiting 5 min')
                sleep(300)
                soup = get_soup(url,mid)
            
            if page_blocked(soup):
                return -1,-1

            # if we overshoot the last page we get sent to the first page,
            # meaning the page number is smaller than mid
            if is_first_page(soup) and (mid != 1):
                high = mid - 1
            elif is_last_page(soup):
                if verbose:
                    print(f'It took {count} {"searches" if count>1 else "search"} to find the last page.')
                
                last_person_rank = get_last_rank(soup)

                return mid, last_person_rank
            else: # we are not on the first or last page, the page we are looking for is larger than mid
                low = mid + 1
        
        # Could not find the last page, we need to change the low/high criteria and start again
        return -1, 0
    
    
    # check that the current last page has not changed
    soup = get_soup(url,last_known_last_page)


    if page_blocked(soup):
        print('Page is blocked... Waiting 5 min')
        sleep(300)
    
    if page_blocked(soup):
        return -1,-1
    
    
    if is_last_page(soup):
        if verbose:
            print('Last Page has not changed')
        
        return last_known_last_page,get_last_rank(soup)
    
    # if we believe the rate of growth will not exceed a set number (i.e. 10 pages per run)
    # we can limit the high end of the binary search to save time
    if estimated_growth_rate > 0:
        low = last_known_last_page - estimated_growth_rate
        high = last_known_last_page + estimated_growth_rate
        lp,lpr = binary_search(low,high,verbose=verbose)
        
        # Page is blocked
        if lp == -1 and lpr == -1:
            return lp,lpr
        # if the page is not found, we extend the binary search to look at all values
        elif lp == -1:
            low = 1
            high = 80000
            return binary_search(low,high,verbose=verbose)
        
        return lp,lpr
        
    else:
        # do a binary search to find the last page
        low = 1
        high = 80000
        return binary_search(low,high,verbose=verbose)  




def update_last_pages_and_ranks(hs_info,verbose=False,estimated_growth_rate=0):
    og_growth = estimated_growth_rate
    for ind, row in hs_info.iterrows():
        # if there is a possible new last page
        if row.Last_Page < 80000:
            if verbose:
                print(f'Checking {row.Skill} for new last page')

            if 'Clue' in row['Skill'] or 'Rift' in row['Skill']:
                estimated_growth_rate = 512
            else:
                estimated_growth_rate = og_growth
                
            lp,lpr = find_last_page_and_rank(row.Last_Page,row.Url,verbose=verbose,estimated_growth_rate=estimated_growth_rate)
            
            if lp != row.Last_Page and (lp != -1):
                print(f'New Last Page found for {row.Skill}, Old: {row.Last_Page}, New: {lp}, Difference: {lp-row.Last_Page}')
                hs_info.loc[ind,'Last_Page'] = lp
                
            if lpr != row.Last_Rank and (lpr != -1) and (lpr != 0):
                print(f'New Last Rank found for {row.Skill}, Old: {row.Last_Rank}, New: {lpr}, Difference: {lpr-row.Last_Rank}')
                hs_info.loc[ind,'Last_Rank'] = lpr

    hs_info.to_csv(hs_info_file_path,index=False)
    
    
def update_specific_last_pages_and_ranks(hs_info,skill,verbose=False,estimated_growth_rate=0):
    last_rank = 0
    og_growth = estimated_growth_rate
    for ind, row in hs_info.iterrows():
        # if there is a possible new last page
        if row.Skill == skill:
            if row.Last_Page < 80000:
                if verbose:
                    print(f'Checking {row.Skill} for new last page')
                
                if 'Clue' in row['Skill'] or 'Rift' in row['Skill']:
                    estimated_growth_rate = 512
                else:
                    estimated_growth_rate = og_growth

                lp,lpr = find_last_page_and_rank(row.Last_Page,row.Url,verbose=verbose,estimated_growth_rate=estimated_growth_rate)
                
                if lp != row.Last_Page and (lp != -1):
                    print(f'New Last Page found for {row.Skill}, Old: {row.Last_Page}, New: {lp}, Difference: {lp-row.Last_Page}')
                    hs_info.loc[ind,'Last_Page'] = lp

                if lpr != row.Last_Rank and (lpr != -1):
                    print(f'New Last Rank found for {row.Skill}, Old: {row.Last_Rank}, New: {lpr}, Difference: {lpr-row.Last_Rank}')
                    hs_info.loc[ind,'Last_Rank'] = lpr
                    last_rank = lpr

    hs_info.to_csv(hs_info_file_path,index=False)
    return last_rank


def calculate_data_for_group(url,total_players):
    
    groups = [0.0001,0.001,0.01, 0.05, 0.2, 0.4, 0.6, 0.8, 1]
    labels = ['Top_0.01%','Top_0.1%','Top_1%','Top_5%','Top_20%','Top_40%','Top_60%','Top_80%', 'Last_Record']
    
    d = {}
    d['Date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    for ind, group in enumerate(groups):
#         print(f'Fetching data for top {group*100}%')
        num_players_in_group = math.floor(group*total_players)
        # calc start and end page
        end_page = num_players_in_group // 25
        remainder = num_players_in_group % 25
        
        if remainder > 0:
            end_page += 1
        
#         print(f'Last player in group is {num_players_in_group} who is on page {end_page}')
        
        soup = get_soup(url, end_page)
        main = soup.find("div", {"id": "contentHiscores"})
        table = main.find("table")
        
        boss = False

        for person in table.findAll("tr",{"class": "personal-hiscores__row"}):
            
            rank = int(person("td")[0].text.strip().replace('\n','').replace(',',''))
            uname = person("td")[1].text.strip().replace('\n','')
            total_level = int(person("td")[2].text.strip().replace('\n','').replace(',',''))
            total_exp = None
            try:
                total_exp = int(person("td")[3].text.strip().replace('\n','').replace(',',''))
            except:
                boss = True
#             print(f'Rank: {rank}, User Name: {uname}, Total Level: {total_level}, Total Exp: {total_exp}')

            if rank == num_players_in_group:
                if total_exp:
                    d[f'{labels[ind]}_total_level'] = [total_level]
                    d[f'{labels[ind]}_total_exp'] = [total_exp]
                    d[f'{labels[ind]}_rank'] = [rank]
                else:
                    d[f'{labels[ind]}_score'] = [total_level]
                    d[f'{labels[ind]}_rank'] = [rank]

        if (labels[ind] == 'Last_Record') and ('Last_Record_score' not in d) and boss:
            d[f'{labels[ind]}_score'] = [np.NaN]
            d[f'{labels[ind]}_rank'] = [np.NaN]
#     print(d)
    return pd.DataFrame(d)



def update_hiscores_files(hs_info):
    for ind, row in hs_info.iterrows():
        egr = 64
        if 'Clue' in row['Skill'] or 'Rift' in row['Skill']:
            egr = 512
        
        new_calc = False
        try:
            new_row = calculate_data_for_group(row.Url,row.Last_Rank)
            if 'Last_Record_score' in new_row.columns:# if this is a boss
                if np.isnan(new_row['Last_Record_score'].iloc[0]):# if there is missing data for the last person (meaning ban has happened?)
                    print('There was an issue finding the last record; Recalculating...')
                    new_calc = True
                    lr = update_specific_last_pages_and_ranks(hs_info,row.Skill,verbose=False,estimated_growth_rate=egr)
                    if lr != 0:
                        new_row = calculate_data_for_group(row.Url,lr)

        except:
            # If we get timed out, wait 10 minutes and then try again
            ten_from_now = (datetime.datetime.now() + datetime.timedelta(minutes = mins)).strftime('%I:%M:%S')
            print(f'A time out occured. Waiting {mins} Minutes. Process will resume at {ten_from_now}')
            sleep(wait_time)
            if new_calc:
                lr = update_specific_last_pages_and_ranks(hs_info,row.Skill,verbose=False,estimated_growth_rate=egr)
                if lr != 0:
                    new_row = calculate_data_for_group(row.Url,lr)
            else:
                new_row = calculate_data_for_group(row.Url,row.Last_Rank)
        
        skill_name = row.Skill.replace('-','').replace(':',' ').replace('(','').replace(')','').replace('\'','').replace('  ',' ').replace(' ','_')

        file_name = f'{hiscores_file_path}{skill_name}_Hiscores.csv'

        if os.path.exists(file_name):
            print(f'Updating file: {file_name}')
            df = pd.read_csv(file_name)
            df = pd.concat([df,new_row],axis=0) 
        else:
            print(f'Creating file: {file_name}')
            df = new_row
        
        df.to_csv(file_name,index=False)
        
        
def update_hiscores_files_start_from(hs_info,start_from_skill):
    start = False
    egr = 64
    if 'Clue' in row['Skill'] or 'Rift' in row['Skill']:
        egr = 512
    
    for ind, row in hs_info.iterrows():
        
        if row.Skill == start_from_skill:
            start = True
        
        if start:

            new_calc = False
            try:
                new_row = calculate_data_for_group(row.Url,row.Last_Rank)
                
                if 'Last_Record_score' in new_row.columns:# if this is a boss
                    if np.isnan(new_row['Last_Record_score'].iloc[0]):# if there is missing data for the last person (meaning ban has happened?)
                        print('There was an issue finding the last record; Recalculating...')
                        new_calc = True
                        lr = update_specific_last_pages_and_ranks(hs_info,row.Skill,verbose=False,estimated_growth_rate=egr)
                        if lr != 0:
                            new_row = calculate_data_for_group(row.Url,lr)
            except:
                # If we get timed out, wait 10 minutes and then try again
                ten_from_now = (datetime.datetime.now() + datetime.timedelta(minutes = mins)).strftime('%I:%M:%S')
                print(f'A time out occured. Waiting {mins} Minutes. Process will resume at {ten_from_now}')
                sleep(wait_time)
                if new_calc:
                    lr = update_specific_last_pages_and_ranks(hs_info,row.Skill,verbose=False,estimated_growth_rate=egr)
                    if lr != 0:
                        new_row = calculate_data_for_group(row.Url,lr)
                else:
                    new_row = calculate_data_for_group(row.Url,row.Last_Rank)

            skill_name = row.Skill.replace('-','').replace(':',' ').replace('(','').replace(')','').replace('\'','').replace('  ',' ').replace(' ','_')

            file_name = f'{hiscores_file_path }{skill_name}_Hiscores.csv'

            if os.path.exists(file_name):
                print(f'Updating file: {file_name}')
                df = pd.read_csv(file_name)
                df = pd.concat([df,new_row],axis=0) 
            else:
                print(f'Creating file: {file_name}')
                df = new_row

            df.to_csv(file_name,index=False)

def check_last_values():
    count = 0
    issues = []
    for i,row in hs_info.iterrows():
        skill_name = row.Skill.replace('-','').replace(':',' ').replace('(','').replace(')','').replace('\'','').replace('  ',' ').replace(' ','_')

        file_name = f'{hiscores_file_path}{skill_name}_Hiscores.csv'
    
        df = pd.read_csv(file_name)
        if 'Last_Record_rank' in df.columns:
            if np.isnan(df['Last_Record_rank'].iloc[-1]):
                count += 1
                print(f'{skill_name} is missing last record')
                issues.append(skill_name)
        iss = pd.DataFrame({'Skill-Boss-Issues':issues})
        file_name = issues_file_path
        iss.to_csv(file_name,index=False)
    return count


print('Reading in CSV')

hs_info = pd.read_csv(hs_info_file_path)

print('Updating Last Pages and Ranks')

update_last_pages_and_ranks(hs_info,verbose=True,estimated_growth_rate=128)

print('Updating Hiscores File')

update_hiscores_files(hs_info)

print('Checking for missing last records')

total_missing = check_last_values()

print(f'Total missing last records: {total_missing}')

sleep(600)


