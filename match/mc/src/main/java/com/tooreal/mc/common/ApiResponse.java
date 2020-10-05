package com.tooreal.mc.common;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ApiResponse {

    private Integer code;

    private String msg;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private Object data;

    @JsonFormat(pattern="yyyy-MM-dd HH:mm:ss",timezone="GMT+8")
    private LocalDateTime localDateTime;

    public static ApiResponse ok(){
        return new ApiResponse(ApiCode.SUCCESS.getCode(), ApiCode.SUCCESS.getMsg(), null, LocalDateTime.now());
    }

    public static ApiResponse ok(Object data){
        return new ApiResponse(ApiCode.SUCCESS.getCode(), ApiCode.SUCCESS.getMsg(), data, LocalDateTime.now());
    }

    public static ApiResponse error(){
        return new ApiResponse(ApiCode.SERVER_INTERNAL_ERROR.getCode(), ApiCode.SERVER_INTERNAL_ERROR.getMsg(), null,
                LocalDateTime.now());
    }

    public static ApiResponse error(String msg){
        return new ApiResponse(ApiCode.SERVER_INTERNAL_ERROR.getCode(), msg, null, LocalDateTime.now());
    }

}
