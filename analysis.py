import json
import os
import pandas as pd
import matplotlib.pyplot as plt

def get_word_count_for_passage(passage, bible_data, day_for_logging):
    """
    Calculates the word count for a single passage, with verse-level precision.
    
    Args:
        passage (str): The passage reference, e.g., "Genesis 1", "Mark 11:3ff".
        bible_data (dict): The dictionary containing all Bible book data.
        day_for_logging (str): The day identifier ("MMDD") for logging errors.

    Returns:
        int: The total word count for the passage.
    """
    try:
        book, reference_str = passage.rsplit(' ', 1)
        book = book.strip()
        reference_str = reference_str.strip()

        if book not in bible_data:
            print(f"On day {day_for_logging}: Book '{book}' not found. (From passage: '{passage}')")
            return 0
        
        book_content = bible_data[book]['chapters']
        word_count = 0

        # --- Main Parsing Logic ---

        # Split reference into chapter and verse parts
        if ':' in reference_str:
            chapter_part, verse_part = reference_str.split(':', 1)
        else:
            chapter_part, verse_part = reference_str, None

        # --- Parse Chapters ---
        chapters_to_process = []
        if '-' in chapter_part:
            start_c, end_c = map(int, chapter_part.split('-'))
            chapters_to_process = list(range(start_c, end_c + 1))
        else:
            chapters_to_process = [int(chapter_part)]
        
        # --- Iterate Over Chapters and Count Words ---
        for i, chap_num in enumerate(chapters_to_process):
            # Default verse range is the entire chapter
            start_v, end_v = 1, -1  # -1 will be replaced with the last verse number

            # Check if the verse part of the reference applies to the current chapter
            # It only applies if it's a single-chapter reference or the last chapter in a range
            is_last_chapter_in_range = (i == len(chapters_to_process) - 1)
            if verse_part and is_last_chapter_in_range:
                if 'ff' in verse_part:
                    start_v = int(verse_part.replace('ff', ''))
                    end_v = -1  # Signifies to the end of the chapter
                elif '-' in verse_part:
                    start_v, end_v = map(int, verse_part.split('-'))
                else:
                    start_v = end_v = int(verse_part)
            
            # Get the chapter data from the loaded bible JSON
            chapter_data = next((c for c in book_content if c['chapter'] == chap_num), None)
            if not chapter_data:
                print(f"On day {day_for_logging}: Chapter {chap_num} not found in book '{book}'.")
                continue

            # Find the actual last verse number if needed
            last_verse_in_chapter = len(chapter_data['verses'])
            if end_v == -1:
                end_v = last_verse_in_chapter
            
            # Sum the words for each verse in the calculated range
            for verse_obj in chapter_data['verses']:
                if start_v <= verse_obj['verse'] <= end_v:
                    word_count += len(verse_obj['text'].split())
        
        return word_count

    except Exception as e:
        print(f"On day {day_for_logging}: Error processing passage '{passage}'. Details: {e}")
        return 0

def calculate_daily_word_counts():
    """
    Parses the McCheyne reading plan and the Bible text to calculate
    the total number of words to be read each day.
    """
    with open('RMM-plan.json', 'r') as f:
        plan = json.load(f)

    bible_path = 'Bible-kjv-1611'
    bible_data = {}
    for filename in os.listdir(bible_path):
        if filename.endswith('.json'):
            book_name = os.path.splitext(filename)[0]
            if book_name not in ["Books", "Books_chapter_count"]:
                with open(os.path.join(bible_path, filename), 'r') as f:
                    bible_data[book_name] = json.load(f)

    daily_word_counts = {}
    for day, readings in plan.items():
        total_words_today = 0
        for reading_type in ['family', 'secret']:
            for passage in readings[reading_type]:
                total_words_today += get_word_count_for_passage(passage, bible_data, day)
        daily_word_counts[day] = total_words_today

    return daily_word_counts

def main():
    """
    Main function to execute the analysis, generate plots, and print statistics.
    """
    daily_word_counts = calculate_daily_word_counts()
    df = pd.DataFrame(list(daily_word_counts.items()), columns=['Day', 'WordCount'])

    df.to_csv('daily_word_counts.csv', index=False)
    print("Daily word counts saved to daily_word_counts.csv")

    plt.figure(figsize=(12, 6))
    plt.hist(df['WordCount'], bins=30, edgecolor='black', alpha=0.7)
    plt.title('Distribution of Daily Word Counts (Verse Accurate)')
    plt.xlabel('Number of Words per Day')
    plt.ylabel('Frequency (Number of Days)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.savefig('word_count_distribution.png')
    print("Distribution plot saved to word_count_distribution.png")
    
    plt.show()

    print("\n--- Summary Statistics for Daily Word Counts (Verse Accurate) ---")
    valid_word_counts = df[df['WordCount'] > 0]['WordCount']
    print(valid_word_counts.describe())

if __name__ == '__main__':
    main()