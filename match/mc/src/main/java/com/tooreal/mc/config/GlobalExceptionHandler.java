package com.tooreal.mc.config;

import com.tooreal.mc.common.ApiResponse;
import com.tooreal.mc.common.CustomException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;

@ControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger LOGGER = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(CustomException.class)
    @ResponseBody
    ApiResponse handleException(CustomException customException){
        LOGGER.error("customException异常：",customException);
        return ApiResponse.error(customException.getException());
    }

    @ExceptionHandler(Exception.class)
    @ResponseBody
    ApiResponse handleException(Exception exception){
        LOGGER.error("未知异常：",exception);
        return ApiResponse.error();
    }
}
