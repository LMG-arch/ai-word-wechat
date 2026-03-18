package com.ai.socialworld.presentation.base

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

abstract class BaseViewModel<T : Any> : ViewModel() {
    private val _stateFlow: MutableStateFlow<T> = MutableStateFlow(createInitialState())
    val stateFlow: StateFlow<T> = _stateFlow.asStateFlow()

    protected val currentState: T
        get() = _stateFlow.value

    abstract fun createInitialState(): T

    protected fun updateState(update: T.() -> T) {
        _stateFlow.value = currentState.update()
    }

    protected fun setState(newState: T) {
        _stateFlow.value = newState
    }
}
