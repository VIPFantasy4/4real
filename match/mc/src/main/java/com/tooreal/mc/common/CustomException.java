package com.tooreal.mc.common;

import lombok.Data;

@Data
public class CustomException extends Exception {
    private String exception;

    public CustomException(String exception){
        super(exception);
        this.exception = exception;
    }
}
