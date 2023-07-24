-- INRIX data along Indian School Rd & 19th Ave (westbound approach)

SELECT t3.timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'US Mountain Standard Time' AS time_mst
    , t1.SegmentID
    , t1.RoadName
    , t1.FRC
    , t1.Miles as Length
    , t3.speed
    , t3.travelTimeMinutes as travelTime
    , t1.StartLat
    , t1.StartLong
    , t1.EndLat
    , t1.EndLong
    , t2.Latitude
    , t2.Longitude
    , t1.Bearing
FROM [ADOT_INRIX].[dbo].[InrixSegments_Geometry] AS t1
LEFT JOIN [ADOT_INRIX].[dbo].[InrixSegments] AS t2
ON t1.SegmentID = t2.ID
LEFT JOIN [ADOT_INRIX].[dbo].[Inrix_Realtime] AS t3
ON t1.SegmentID = t3.SegmentID
WHERE t1.SegmentID IN ('450124848', '450124851')
    AND t1.Bearing = 'W'
    AND t3.timestamp BETWEEN '2023-01-01 07:00:00' AND '2023-02-28 06:59:59' /* query UTC times */
ORDER BY t3.timestamp