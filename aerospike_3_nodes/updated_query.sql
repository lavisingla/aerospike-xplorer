-- Declare variables for each FIGI value
DECLARE @figi1 nvarchar(4000) = 'BBG000DQSHL6';
DECLARE @figi2 nvarchar(4000) = 'BBG000BYLJ52';
DECLARE @figi3 nvarchar(4000) = 'BBG00L1BBGW4';
DECLARE @figi4 nvarchar(4000) = 'BBG000BC16D1';
DECLARE @figi5 nvarchar(4000) = 'BBG000BCDQ35';
DECLARE @figi6 nvarchar(4000) = 'BBG000BCFRQ6';
DECLARE @figi7 nvarchar(4000) = 'BBG000W907Q0';
DECLARE @figi8 nvarchar(4000) = 'BBG000BCCNZ8';
DECLARE @figi9 nvarchar(4000) = 'BBG000DVJ6L9';
DECLARE @figi10 nvarchar(4000) = 'BBG000BCB3M7';
DECLARE @figi11 nvarchar(4000) = 'BBG01TMPW438';
DECLARE @figi12 nvarchar(4000) = 'BBG000BC9MR3';
DECLARE @figi13 nvarchar(4000) = 'BBG000BBXV34';
DECLARE @figi14 nvarchar(4000) = 'BBG000BWBBP2';
DECLARE @figi15 nvarchar(4000) = 'BBG000BBXJ95';
DECLARE @figi16 nvarchar(4000) = 'BBG000BBY7M5';
DECLARE @figi17 nvarchar(4000) = 'BBG000BDYY97';
DECLARE @figi18 nvarchar(4000) = 'BBG000BKD864';
DECLARE @figi19 nvarchar(4000) = 'BBG000CSHJP7';
DECLARE @figi20 nvarchar(4000) = 'BBG000LHT4L5';
DECLARE @figi21 nvarchar(4000) = 'BBG000BH7B07';
DECLARE @figi22 nvarchar(4000) = 'BBG000BP01S8';
DECLARE @figi23 nvarchar(4000) = 'BBG01RLW85S5';
DECLARE @figi24 nvarchar(4000) = 'BBG000BC86D4';
DECLARE @figi25 nvarchar(4000) = 'BBG000BCB150';
DECLARE @figi26 nvarchar(4000) = 'BBG000BC98G6';
DECLARE @figi27 nvarchar(4000) = 'BBG000BHHK06';
DECLARE @figi28 nvarchar(4000) = 'BBG000C1M4K8';
DECLARE @figi29 nvarchar(4000) = 'BBG000CSHLR0';
DECLARE @figi30 nvarchar(4000) = 'BBG000BC7Q05';
DECLARE @figi31 nvarchar(4000) = 'BBG000NH2RJ4';
DECLARE @figi32 nvarchar(4000) = 'BBG000BDXBJ7';
DECLARE @figi33 nvarchar(4000) = 'BBG000BBWCH2';
DECLARE @figi34 nvarchar(4000) = 'BBG000BBY1B0';
DECLARE @figi35 nvarchar(4000) = 'BBG000BC84V9';
DECLARE @figi36 nvarchar(4000) = 'BBG000BC8029';
DECLARE @figi37 nvarchar(4000) = 'BBG000BBY8X1';
DECLARE @figi38 nvarchar(4000) = 'BBG01RMZNZJ4';
DECLARE @figi39 nvarchar(4000) = 'BBG000GVXC37';
DECLARE @figi40 nvarchar(4000) = 'BBG000BJNPL1';
DECLARE @figi41 nvarchar(4000) = 'BBG000BLGLW1';
DECLARE @figi42 nvarchar(4000) = 'BBG000BB4980';
DECLARE @figi43 nvarchar(4000) = 'BBG00YRS5632';

-- Updated query using variables
SELECT s.spn 
FROM security_master.sec.basic_latest_custom_search s WITH (NOLOCK) 
WHERE 1=1 
AND ( 
    s.bbg_figi IN ( 
        @figi1, @figi2, @figi3, @figi4, @figi5, @figi6, @figi7, @figi8, @figi9, @figi10,
        @figi11, @figi12, @figi13, @figi14, @figi15, @figi16, @figi17, @figi18, @figi19, @figi20,
        @figi21, @figi22, @figi23, @figi24, @figi25, @figi26, @figi27, @figi28, @figi29, @figi30,
        @figi31, @figi32, @figi33, @figi34, @figi35, @figi36, @figi37, @figi38, @figi39, @figi40,
        @figi41, @figi42, @figi43
    ) 
) 
AND s.birth != s.death
