graph TD
    A[/main.py\] --> B[video_downloader.py]
    A --> C[video_processor.py]
    A --> D[new_final_report_generator.py]
    A --> E[api_statistics.py]

    subgraph "1. Video Download"
        B ==>|async: get_video_info| F[(YouTube)]
        F ==>|async: download_youtube_video| G[/Video Chunks\]
        G ==>|async: split_video_into_chunks| PA[Performance: 45.03s]
    end

    subgraph "2. Video Processing"
        C ==>|async: upload_video| H[file_uploader.py]
        C ==>|async: process_video| I[content_generator.py]
        H ==>|async: check_video_status| HA[Upload Chunks]
        I ==>|async: analyze_video_content| IA[Analyze Video]
        I ==>|async: analyze_transcript| IB[Analyze Transcript]
        I ==>|async: analyze_intertextual_references| IC[Analyze Intertextual]
        IA & IB & IC ==>|async: save_interim_work_product| ID[/Interim Work Products\]
        ID ==>|async: consolidate_analyses| J[/Consolidated Analyses\]
        J --> PB[Performance: 191.47s]
        ID --> PC[Avg 7.46s per chunk]
    end

    subgraph "3. Report Generation"
        D ==>|async: load_work_products| K[/Load Interim Work Products\]
        K ==>|async: generate_integrated_report| L[/Generate Final Report\]
        L --> PD[Performance: 227.54s]
    end

    subgraph "API Interaction"
        M[models.py]
        M ==>|async: get_gemini_flash_model_text| N[Gemini Flash Model]
        M ==>|async: get_final_report_model_text| O[Gemini Pro Model]
        E ==>|async: record_call, record_process| P[/API Statistics\]
        P --> PE[Total Runtime: 465.01s]
    end

    subgraph "Utilities"
        Q[utils.py]
        R[error_handling.py]
    end

    A -.->|Use| M
    A -.->|Use| Q
    A -.->|Use| R
    C -.->|Use| M
    D -.->|Use| M
    I -.->|Use| M

    subgraph "Chart Key"
        K1[Process]
        K2[/Data\]
        K3[(External System)]
        K4[API Component]
        K5[Performance Metric]
        K6[Async Operation]
    end

    subgraph "Module List"
        ML["
        - main.py
        - video_downloader.py
        - video_processor.py
        - new_final_report_generator.py
        - api_statistics.py
        - file_uploader.py
        - content_generator.py
        - models.py
        - utils.py
        - error_handling.py
        "]
    end

    subgraph "Key Functions"
        KF["
        - get_video_info()
        - download_youtube_video()
        - process_video()
        - analyze_video_content()
        - analyze_transcript()
        - analyze_intertextual_references()
        - generate_integrated_report()
        - record_call()
        - record_process()
        - generate_report()
        "]
    end

    subgraph "Major Libraries"
        LIB["
        - google.generativeai
        - yt_dlp
        - moviepy
        - aiofiles
        - youtube_transcript_api
        - pytube
        "]
    end

    classDef process fill:#f9f,stroke:#333,stroke-width:2px;
    classDef data fill:#bbf,stroke:#333,stroke-width:2px;
    classDef external fill:#fcc,stroke:#333,stroke-width:2px;
    classDef api fill:#bfb,stroke:#333,stroke-width:2px;
    classDef performance fill:#ffb,stroke:#333,stroke-width:2px;
    classDef list fill:#efe,stroke:#333,stroke-width:2px;
    classDef async stroke:#f66,stroke-width:4px;
    class A,B,C,D,H,I,HA,IA,IB,IC,K1 process;
    class G,ID,J,K,L,P,K2 data;
    class F,K3 external;
    class M,N,O,K4 api;
    class PA,PB,PC,PD,PE,K5 performance;
    class ML,KF,LIB list;

    style K1 fill:#f9f,stroke:#333,stroke-width:2px
    style K2 fill:#bbf,stroke:#333,stroke-width:2px
    style K3 fill:#fcc,stroke:#333,stroke-width:2px
    style K4 fill:#bfb,stroke:#333,stroke-width:2px
    style K5 fill:#ffb,stroke:#333,stroke-width:2px
    style K6 stroke:#f66,stroke-width:4px