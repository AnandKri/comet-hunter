# Detailed Pipeline for processed_file_repository

Explaining the file lifecycle

1. States [ all possible states for a given file ]
    - DISCOVERED : raw file is available in the NASA opendirectory
    - DOWNLOADING : file downloading to local has begun
    - DOWNLOADED : file successfully downloaded to local
    - DOWNLOAD_FAILED : file failed to download successfully
    - RETRY_DOWNLOAD : file to be retried for downloading, after `DOWNLOAD_FAILED`
    - IGNORE : file to be ignored for downloading, maximum retries reached for downloading it
    - IDLE : file is in local
    - SKIPPED : file which are not eligible for processing; based on metadata or outdated timestamp
    - READY : files eligible for processing (`RETRY_PROCESSING` files also come here)  
    - PROCESSING : file processing started
    - PROCESSED : file successfully processed
    - PROCESSING_FAILED : file failed to process successfully
    - RETRY_PROCESSING : file in queue for `again` processing
    - ABANDONED : file has failed to be processed and has reached maximum limit for retry attempts at processing 

2. Terminal States  
    - IGNORE
    - SKIPPED
    - PROCESSED
    - ABANDONED  

3. Transitions [ how the state transition will take place ]
    - DISCOVERED &#10145; DOWNLOADING
    - DOWNLOADING &#10145; DOWNLOAD_FAILED
    - DOWNLOADING &#10145; DOWNLOADED
    - DOWNLOAD_FAILED &#10145; RETRY_DOWNLOAD
    - RETRY_DOWNLOAD &#10145; DOWNLOADING
    - RETRY_DOWNLOAD &#10145; IGNORE
    - DOWNLOADED &#10145; IDLE
    - IDLE &#10145; SKIPPED
    - IDLE &#10145; READY
    - READY &#10145; PROCESSING
    - PROCESSING &#10145; PROCESSING_FAILED
    - PROCESSING &#10145; PROCESSED
    - PROCESSING_FAILED &#10145; RETRY_PROCESSING
    - PROCESSING_FAILED &#10145; ABANDONED
    - RETRY_PROCESSING &#10145; READY

4. Scenarios [ what does a normal, failure and other particular scenarios look like ]
    - Normal workflow  
    DISCOVERED &#10145; DOWNLOADING &#10145; DOWNLOADED &#10145; IDLE &#10145; READY &#10145; PROCESSING &#10145; PROCESSED  

    - Failure1 workflow [ file failed to be downloaded ]  
    DISCOVERED &#10145; DOWNLOADING &#10145; DOWNLOAD_FAILED &#10145; max_limit[ RETRY_DOWNLOAD &#10145; DOWNLOADING &#10145; DOWNLOAD_FAILED ] &#10145; IGNORE
    - Failure2 workflow [ file skipped for processing ]  
    DISCOVERED &#10145; DOWNLOADING &#10145; DOWNLOADED &#10145; IDLE &#10145; SKIPPED  
    - Failure3 workflow [ file failed to be processed ]  
    DISCOVERED &#10145; DOWNLOADING &#10145; DOWNLOADED &#10145; IDLE &#10145; READY &#10145; PROCESSING &#10145; PROCESSING_FAILED &#10145; max_limit[ RETRY_PROCESSING &#10145; PROCESSING &#10145; PROCESSING_FAILED ] &#10145; ABANDONED  
    - Failure4 workflow [ file failed to download due to timeout ]  
    DISCOVERED &#10145; DOWNLOADING &#10145; `timeout` &#10145; DOWNLOAD_FAILED...  
    - Failure5 workflow [ file failed to process due to timeout ]  
    DISCOVERED &#10145; DOWNLOADING &#10145; DOWNLOADED &#10145; IDLE &#10145; READY &#10145; PROCESSING &#10145; `timeout` &#10145; PROCESSING_FAILED...   
    - Failure6 workflow [ worker crash during download ]  
    DISCOVERED &#10145; DOWNLOADING &#10145; `system crash` &#10145; `timeout recovery` &#10145; DOWNLOAD_FAILED...  
    - Failure7 workflow [ worker crash during processing ]
    DISCOVERED &#10145; DOWNLOADING &#10145; DOWNLOADED &#10145; IDLE &#10145; READY &#10145; PROCESSING &#10145; `system crash` &#10145;  `timeout recovery` &#10145; PROCESSING_FAILED...  
    - Failure8 workflow [ duplicate discovery attempt ]
    DISCOVERED &#10145; `metadata poll again` &#10145; `ignore due to unique constraint`  
    `raw_file_hash` is unique

5. Failure recovery
    - Download recovery  
    
    `DOWNLOADING` AND `now - download_started_at > download_timeout` AND `download_attempts < max_download_attempts` &#10145; `RETRY_DOWNLOAD`  

    `DOWNLOADING` AND `now - download_started_at > download_timeout` AND `download_attempts >= max_download_attempts` &#10145; `IGNORE`  

    - Processing recovery  
    
    `PROCESSING` AND `now - processing_started_at > processing_timeout` AND `processing_attempts < max_processing_attempts` &#10145; `RETRY_PROCESSING`

    `PROCESSING` AND `now - processing_started_at > processing_timeout` AND `processing_attempts >= max_processing_attempts` &#10145; `ABANDONED`  

    - Corruption validation  
    `DOWNLOADED` &#10145; `DOWNLOAD_FAILED`  
    When file validation fails. File validation metrics could be filesize, invalid format, failure to read etc.  
    
6. Retry policy  
    - Download  
    Retry when `DOWNLOAD_FAILED`  
    download_attempts < max_download_attempts  
    Retry occurs immediately  
    download_attempts incremented when download attempt begins    
    If download_attempts exceeded &#10145; `IGNORE`

    - Processing  
    Retry when `PROCESSING_FAILED`  
    processing_attempts < max_processing_attempts  
    Retry occurs immediately  
    processing_attempts incremented when processing begins  
    If processing_attempts exceeded &#10145; `ABANDONED`