from googleapiclient.discovery import build
import pymongo
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import pandas as pd
import mysql.connector

client = pymongo.MongoClient("mongodb://sheikmuzzammil:khamilabanu@ac-0zbysir-shard-00-00.6t66exf.mongodb.net:27017,ac-0zbysir-shard-00-01.6t66exf.mongodb.net:27017,ac-0zbysir-shard-00-02.6t66exf.mongodb.net:27017/?ssl=true&replicaSet=atlas-8wvq96-shard-0&authSource=admin&retryWrites=true&w=majority")
db = client["YoutubeDB"]

mydb = mysql.connector.connect(host="127.0.0.1",
                               user='root',
                               password='Passw0rd!sql',
                               database="ytdata",
                               port="3306"
                               )
mycursor=mydb.cursor(buffered=True)

st.set_page_config(page_title="Youtube Data Harvesting", page_icon="",layout="wide", initial_sidebar_state="expanded")

st.markdown('<h1 style="color: red;">Youtube Data Harvesting & Warehousing </h1>', unsafe_allow_html=True)

with st.sidebar:
    selected = option_menu(None, ["Home","Extract and Transform","Sql Query","About"],
                           icons=["house-door-fill","tools","card-text","exclamation-circle"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "21px", "text-align": "centre", "margin": "0px",
                                                "--hover-color": "#F70404"},
                                   "icon": {"font-size": "30px"},
                                   "container" : {"max-width": "6000px"},
                                   "nav-link-selected": {"background-color": "#F70404"}})


api_key = "AIzaSyDHQkyVPGoX6fIETPSMgy0qJ_FJcvWT8DM"
youtube = build('youtube','v3',developerKey=api_key)

def get_channel_details(channel_id):
    ch_data = []
    response = youtube.channels().list(part = 'snippet,contentDetails,statistics',
                                     id= channel_id).execute()

    for i in range(len(response['items'])):
        data = dict(Channel_id=channel_id[i],
                    Channel_name=response['items'][i]['snippet']['title'],
                    Playlist_id=response['items'][i]['contentDetails']['relatedPlaylists']['uploads'],
                    Subscribers=response['items'][i]['statistics']['subscriberCount'],
                    Views=response['items'][i]['statistics']['viewCount'],
                    Total_videos=response['items'][i]['statistics']['videoCount'],
                    Description=response['items'][i]['snippet']['description'],
                    Country=response['items'][i]['snippet'].get('country')
                    )
        ch_data.append(data)
    return ch_data


# FUNCTION TO GET VIDEO IDS
def get_channel_videos(channel_id):
    video_ids = []
    # get Uploads playlist id
    res = youtube.channels().list(id=channel_id,
                                  part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None

    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id,
                                           part='snippet',
                                           maxResults=50,
                                           pageToken=next_page_token).execute()

        for i in range(len(res['items'])):
            video_ids.append(res['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = res.get('nextPageToken')

        if next_page_token is None:
            break
    return video_ids


# FUNCTION TO GET VIDEO DETAILS
def get_video_details(v_ids):
    video_stats = []

    for i in range(0, len(v_ids), 50):
        response = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(v_ids[i:i + 50])).execute()
        for video in response['items']:
            video_details = dict(Channel_name=video['snippet']['channelTitle'],
                                 Channel_id=video['snippet']['channelId'],
                                 Video_id=video['id'],
                                 Title=video['snippet']['title'],
                                 Tags=video['snippet'].get('tags'),
                                 Thumbnail=video['snippet']['thumbnails']['default']['url'],
                                 Description=video['snippet']['description'],
                                 Published_date=video['snippet']['publishedAt'],
                                 Duration=video['contentDetails']['duration'],
                                 Views=video['statistics']['viewCount'],
                                 Likes=video['statistics'].get('likeCount'),
                                 Comments=video['statistics'].get('commentCount'),
                                 Favorite_count=video['statistics']['favoriteCount'],
                                 Definition=video['contentDetails']['definition'],
                                 Caption_status=video['contentDetails']['caption']
                                 )
            video_stats.append(video_details)
    return video_stats

# FUNCTION TO GET COMMENT DETAILS
def get_comments_details(v_id):
    comment_data = []
    try:
        next_page_token = None
        while True:
            response = youtube.commentThreads().list(part="snippet,replies",
                                                    videoId=v_id,
                                                    maxResults=100,
                                                    pageToken=next_page_token).execute()
            for cmt in response['items']:
                data = dict(Comment_id = cmt['id'],
                            Video_id = cmt['snippet']['videoId'],
                            Comment_text = cmt['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_author = cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_posted_date = cmt['snippet']['topLevelComment']['snippet']['publishedAt'],
                            Like_count = cmt['snippet']['topLevelComment']['snippet']['likeCount'],
                            Reply_count = cmt['snippet']['totalReplyCount']
                           )
                comment_data.append(data)
            next_page_token = response.get('nextPageToken')
            if next_page_token is None:
                break
    except:
        pass
    return comment_data

# FUNCTION TO GET CHANNEL NAMES FROM MONGODB
def channel_names():
    ch_name = []
    for i in db.channel_details.find():
        ch_name.append(i['Channel_name'])
    return ch_name



if selected == 'Home':

    st.markdown('__<p style="font-family: verdana; text-align:left; font-size: 15px; color: #008FFF">Our web application provides an interactive platform to explore YouTube channels and their content. With just the YouTube channel ID, you can retrieve comprehensive information about any channel and dive into its details.</P>__',
                unsafe_allow_html=True)

    st.markdown("""

    Features:

        * Channel Overview: Get a quick overview of the channel, including its name, description, and subscriber count. This gives you a snapshot of the channel's popularity and focus. Upon overview of channel, we can proceed with harvest option to collect complete information about the channel and store it in our databae

        * No Structured Data Storage: We store the retrieved channel information in our MongoDB database. This ensures that the data is securely stored and readily available for future use.

        * Migration to PostgreSQL: To enhance data analysis and reporting capabilities, we migrate the stored channel information to a structured PostgreSQL database. This allows for efficient querying and data manipulation, enabling us to extract valuable insights from the stored data.

        * Currently, we are in the first stage of our YouTube analytics project which focuses on FAQs for the channels. To make it easier to get answers, we've added a tab entitled "FAQ" that will give responses based on harvested channels.


        * Our web application leverages the power of YouTube's API and combines it with the versatility of MongoDB and PostgreSQL databases. This combination ensures a seamless user experience while providing robust data management and analysis capabilities.

        * Start exploring YouTube channels like never before! Enter the YouTube channel ID, and our web application will provide you with a comprehensive overview of the channel, its latest and popular videos, and much more.

        Enjoy your journey through the world of YouTube channels with our web application!.""")

    st.markdown("### :green[Domain] : Social Media 💻")
    st.markdown("### :orange[Technologies used] : Python,MongoDB, Youtube Data API, MySql, Streamlit")


if selected =="Extract and Transform":
    tab1, tab2 = st.tabs(["$\huge 📝🎈 GET DATA $", "$\huge 🚀  TRANSFORM TO SQL $"])

    # GET DATA TAB
    with tab1:
        st.markdown("#    ")
        st.write("### Enter YouTube Channel_ID below :")
        ch_id = st.text_input(
            "Hint : Goto channel's home page > Right click > View page source > Find channel_id").split(',')

        if ch_id and st.button("Extract Data"):
            ch_details = get_channel_details(ch_id)
            st.write(f'#### Extracted data from :green["{ch_details[0]["Channel_name"]}"] channel')
            st.table(ch_details)
            st.success("Extract successful !!", icon="✅")

        if st.button("Upload to MongoDB"):
            with st.spinner('Please Wait for a while...'):
                ch_details = get_channel_details(ch_id)
                v_ids = get_channel_videos(ch_id)
                vid_details = get_video_details(v_ids)


                def comments():
                    com_d = []
                    for i in v_ids:
                        com_d += get_comments_details(i)
                    return com_d


                comm_details = comments()

                collections1 = db.channel_details
                collections1.insert_many(ch_details)

                collections2 = db.video_details
                collections2.insert_many(vid_details)

                collections3 = db.comments_details
                collections3.insert_many(comm_details)
                st.success("Upload to MongoDB successful !!",icon="✅")

        # TRANSFORM TAB
    with tab2:
        st.markdown("#   ")
        st.markdown("### Select a channel to begin Transformation to SQL")

        ch_names = channel_names()
        user_inp = st.selectbox("Select channel", options=ch_names)


        def insert_into_channels():
            collections = db.channel_details
            query = """INSERT INTO channels VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"""

            for i in collections.find({"Channel_name": user_inp}, {'_id': 0}):
                mycursor.execute(query, tuple(i.values()))
                mydb.commit()


        def insert_into_videos():
            collections1 = db.video_details
            query1 = """INSERT INTO videos VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

            for i in collections1.find({"Channel_name": user_inp}, {'_id': 0}):
                mycursor.execute(query1, tuple(i.values()))
                mydb.commit()


        def insert_into_comments():
            collections1 = db.video_details
            collections2 = db.comments_details
            query2 = """INSERT INTO comments VALUES(%s,%s,%s,%s,%s,%s,%s)"""

            for vid in collections1.find({"Channel_name": user_inp}, {'_id': 0}):
                for i in collections2.find({'Video_id': vid['Video_id']}, {'_id': 0}):
                    mycursor.execute(query2, tuple(i.values()))
                    mydb.commit()


        if st.button("Submit"):
            try:
                insert_into_channels()
                insert_into_videos()
                insert_into_comments()

                st.success("Transformation to MySQL Successful !!",icon="✅")


            except:
                st.error("Channel details already transformed !!")


if selected =="Sql Query":
    st.write("## :orange[Select any question to get Insights]")
    questions = st.selectbox('Questions',
                             ['1. What are the names of all the videos and their corresponding channels?',
                              '2. Which channels have the most number of videos, and how many videos do they have?',
                              '3. What are the top 10 most viewed videos and their respective channels?',
                              '4. How many comments were made on each video, and what are their corresponding video names?',
                              '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
                              '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
                              '7. What is the total number of views for each channel, and what are their corresponding channel names?',
                              '8. What are the names of all the channels that have published videos in the year 2022?',
                              '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
                              '10. Which videos have the highest number of comments, and what are their corresponding channel names?'])

    if questions == '1. What are the names of all the videos and their corresponding channels?':
        mycursor.execute("""SELECT title AS Video_Title, channel_name AS Channel_Name
                                FROM videos
                                ORDER BY channel_name""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)

    elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, total_videos AS Total_Videos
                                FROM channels
                                ORDER BY total_videos DESC""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Number of videos in each channel :]")
        # st.bar_chart(df,x= mycursor.column_names[0],y= mycursor.column_names[1])
        fig = px.bar(df,
                     x=mycursor.column_names[0],
                     y=mycursor.column_names[1],
                     orientation='v',
                     color=mycursor.column_names[0]
                     )
        st.plotly_chart(fig, use_container_width=True)

    elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, title AS Video_Title, views AS Views 
                              FROM videos
                              ORDER BY views DESC
                              LIMIT 10""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Top 10 most viewed videos :]")
        fig = px.bar(df,
                     x=mycursor.column_names[2],
                     y=mycursor.column_names[1],
                     orientation='h',
                     color=mycursor.column_names[0]
                     )
        st.plotly_chart(fig, use_container_width=True)


    elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
        mycursor.execute("""SELECT a.video_id AS Video_id, a.title AS Video_Title, b.Total_Comments
                              FROM videos AS a
                              LEFT JOIN (SELECT video_id,COUNT(comment_id) AS Total_Comments
                              FROM comments GROUP BY video_id) AS b
                              ON a.video_id = b.video_id
                              ORDER BY b.Total_Comments DESC""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)

    elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name,title AS Title,likes AS Likes_Count 
                               FROM videos
                               ORDER BY likes DESC
                               LIMIT 10""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Top 10 most liked videos :]")
        fig = px.bar(df,
                     x=mycursor.column_names[2],
                     y=mycursor.column_names[1],
                     orientation='h',
                     color=mycursor.column_names[0]
                     )
        st.plotly_chart(fig, use_container_width=True)



    elif questions == '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
        mycursor.execute("""SELECT title AS Title, likes AS Likes_Count
                               FROM videos
                               ORDER BY likes DESC""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)

    elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, views AS Views
                               FROM channels
                               ORDER BY views DESC""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Channels vs Views :]")
        fig = px.bar(df,
                     x=mycursor.column_names[0],
                     y=mycursor.column_names[1],
                     orientation='v',
                     color=mycursor.column_names[0]
                     )
        st.plotly_chart(fig, use_container_width=True)



    elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
        mycursor.execute("""SELECT channel_name AS Channel_Name
                               FROM videos
                               WHERE published_date LIKE '2022%'
                               GROUP BY channel_name
                               ORDER BY channel_name""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)

    elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name,
                                AVG(duration)/60 AS "Average_Video_Duration (mins)"
                                FROM videos
                                GROUP BY channel_name
                                ORDER BY AVG(duration)/60 DESC""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Avg video duration for channels :]")
        fig = px.bar(df,
                     x=mycursor.column_names[0],
                     y=mycursor.column_names[1],
                     orientation='v',
                     color=mycursor.column_names[0]
                     )
        st.plotly_chart(fig, use_container_width=True)



    elif questions == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name,video_id AS Video_ID,comments AS Comments
                                FROM videos
                                ORDER BY comments DESC
                                LIMIT 10""")
        df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Videos with most comments :]")
        fig = px.bar(df,
                     x=mycursor.column_names[1],
                     y=mycursor.column_names[2],
                     orientation='v',
                     color=mycursor.column_names[0]
                     )
        st.plotly_chart(fig, use_container_width=True)

if selected =="About":
    st.markdown('__<p style="text-align:left; font-size: 30px; color: #FAA026">Youtube Data Harvesting</P>__',
                unsafe_allow_html=True)

    st.markdown("For any feedback/suggestion can contact through:")
    st.subheader("LinkedIn")
    st.write("www.linkedin.com/in/sheik-muzzammil/")
    st.subheader("Email ID")
    st.write("sheikmuzzammil4416@gmail.com")
    st.subheader("Github")
    st.write("https://github.com/sheik-muzzammil")
